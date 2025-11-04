# leaderboard/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import uuid

EX = "http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#"

sparql_update = SPARQLWrapper("http://localhost:3030/trelix/update")
sparql_select = SPARQLWrapper("http://localhost:3030/trelix/sparql")

def run_update(query):
    try:
        sparql_update.setMethod(POST)
        sparql_update.setQuery(query)
        sparql_update.query()
    except Exception as e:
        print(f"Update failed: {e}")  # Log it

# leaderboard/views.py

def run_select(query):
    sparql_select.setQuery(query)
    sparql_select.setReturnFormat(JSON)
    response = sparql_select.query().convert()

    # ASK query → returns {'boolean': True/False}
    if 'boolean' in response:
        return [{'boolean': str(response['boolean']).lower()}]

    # SELECT query → return bindings
    return response.get('results', {}).get('bindings', [])


# Helper
def iri(id_str):
    return f"<{EX}{id_str}>"


# CREATE QUIZ
def quiz_create(request):
    if request.method == 'POST':
        quiz_id = str(uuid.uuid4())
        title = request.POST['quizTitle'].strip()
        if not title:
            return render(request, 'quiz/quiz_create.html', {'error': 'Title required'})

        quiz_iri = iri(quiz_id)

        # Insert Quiz
        run_update(f"""
        PREFIX ex: <{EX}>
        INSERT DATA {{ {quiz_iri} a ex:Quiz ; ex:quizTitle "{title}" }}
        """)

        # Parse ONE question
        q_text = request.POST.get('questions[0][text]', '').strip()
        if q_text:
            q_id = str(uuid.uuid4())
            q_iri = iri(q_id)

            run_update(f"""
            PREFIX ex: <{EX}>
            INSERT DATA {{
                {q_iri} a ex:Question ; ex:questionText "{q_text}" .
                {quiz_iri} ex:hasQuestion {q_iri} .
            }}
            """)

            for i in range(4):
                c_text = request.POST.get(f'questions[0][choices][{i}][text]', '').strip()
                if not c_text:
                    continue
                c_correct = request.POST.get(f'questions[0][choices][{i}][isCorrect]') == 'on'
                c_id = str(uuid.uuid4())
                c_iri = iri(c_id)

                run_update(f"""
                PREFIX ex: <{EX}>
                INSERT DATA {{
                    {c_iri} a ex:Choice ;
                        ex:choiceText "{c_text}" ;
                        ex:isCorrect {"true" if c_correct else "false"} .
                    {q_iri} ex:hasChoice {c_iri} .
                }}
                """)

        return redirect('quiz_list')

    return render(request, 'quiz/quiz_create.html')


# LIST QUIZZES
def quiz_list(request):
    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?quiz ?title WHERE {{ ?quiz a ex:Quiz ; ex:quizTitle ?title }}
    """)
    quizzes = [
        {'id': r['quiz']['value'].split('#')[-1], 'title': r['title']['value']}
        for r in results
    ]
    return render(request, 'quiz/quiz_list.html', {'quizzes': quizzes})


# QUIZ DETAIL
def quiz_detail(request, quiz_id):
    quiz_iri = iri(quiz_id)
    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?title WHERE {{ {quiz_iri} a ex:Quiz ; ex:quizTitle ?title }}
    """)
    if not results:
        return HttpResponseNotFound("Quiz not found")
    title = results[0]['title']['value']
    return render(request, 'quiz/quiz_detail.html', {'quiz_id': quiz_id, 'title': title})


# JOIN QUIZ
def join_quiz(request, quiz_id):
    if request.method == 'POST':
        player_name = request.POST.get('player_name', 'Anonymous').strip() or 'Anonymous'
        request.session['player_name'] = player_name
        request.session['quiz_id'] = quiz_id
        return redirect('quiz_take', quiz_id=quiz_id)

    quiz_iri = iri(quiz_id)
    query = f"""
    PREFIX ex: <{EX}>
    ASK WHERE {{ {quiz_iri} a ex:Quiz }}
    """

    try:
        result = run_select(query)
        exists = bool(result) and result[0].get('boolean') == 'true'
        if not exists:
            return HttpResponseNotFound(f"Quiz with ID {quiz_id} not found.")
    except Exception as e:
        return HttpResponseNotFound(f"SPARQL Error: {str(e)}")

    return render(request, 'quiz/join_quiz.html', {'quiz_id': quiz_id})


# TAKE QUIZ
def quiz_take(request, quiz_id):
    if request.session.get('quiz_id') != quiz_id or not request.session.get('player_name'):
        return redirect('join_quiz', quiz_id=quiz_id)

    quiz_iri = iri(quiz_id)
    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?question ?text ?choice ?choiceText ?isCorrect WHERE {{
        {quiz_iri} ex:hasQuestion ?question .
        ?question ex:questionText ?text ; ex:hasChoice ?choice .
        ?choice ex:choiceText ?choiceText ; ex:isCorrect ?isCorrect .
    }}
    """)

    questions = {}
    for r in results:
        q_iri = r['question']['value']
        qid = q_iri.split('#')[-1]
        if qid not in questions:
            questions[qid] = {'id': qid, 'text': r['text']['value'], 'choices': []}
        questions[qid]['choices'].append({
            'text': r['choiceText']['value'],
            'isCorrect': r['isCorrect']['value'] == 'true'
        })

    if request.method == 'POST':
        return redirect('quiz_submit', quiz_id=quiz_id)

    return render(request, 'quiz/quiz_take.html', {
        'quiz_id': quiz_id,
        'player_name': request.session['player_name'],
        'questions': list(questions.values())
    })


# SUBMIT & SCORE
def quiz_submit(request, quiz_id):
    player_name = request.session.get('player_name')
    if not player_name or request.session.get('quiz_id') != quiz_id:
        return redirect('join_quiz', quiz_id=quiz_id)

    quiz_iri = iri(quiz_id)
    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?question ?text ?choice ?choiceText ?isCorrect WHERE {{
        {quiz_iri} ex:hasQuestion ?question .
        ?question ex:questionText ?text ; ex:hasChoice ?choice .
        ?choice ex:choiceText ?choiceText ; ex:isCorrect ?isCorrect .
    }}
    """)

    questions = {}
    for r in results:
        q_iri = r['question']['value']
        qid = q_iri.split('#')[-1]
        if qid not in questions:
            questions[qid] = {'text': r['text']['value'], 'correct': None}
        if r['isCorrect']['value'] == 'true':
            questions[qid]['correct'] = r['choiceText']['value']

    score = sum(1 for qid, q in questions.items() if request.POST.get(qid) == q['correct'])
    total = len(questions)

    entry_id = str(uuid.uuid4())
    entry_iri = iri(entry_id)

    run_update(f"""
    PREFIX ex: <{EX}>
    INSERT DATA {{
        {entry_iri} a ex:QCM_Leaderboard ;
            ex:playerName "{player_name}" ;
            ex:score {score} ;
            ex:totalQuestions {total} ;
            ex:forQuiz {quiz_iri} .
    }}
    """)

    request.session.pop('player_name', None)
    request.session.pop('quiz_id', None)

    return render(request, 'quiz/quiz_result.html', {
        'score': score, 'total': total, 'quiz_id': quiz_id
    })


# LEADERBOARD PER QUIZ
def quiz_leaderboard(request, quiz_id):
    quiz_iri = iri(quiz_id)
    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?player ?score ?total WHERE {{
        ?e a ex:QCM_Leaderboard ;
           ex:playerName ?player ;
           ex:score ?score ;
           ex:totalQuestions ?total ;
           ex:forQuiz {quiz_iri} .
    }} ORDER BY DESC(?score)
    """)
    entries = []
    for r in results:
        score = int(r['score']['value'])
        total = int(r['total']['value'])
        percent = round((score / total) * 100, 0) if total > 0 else 0
        entries.append({
            'player': r['player']['value'],
            'score': score,
            'total': total,
            'percent': percent,
        })
    return render(request, 'quiz/quiz_leaderboard.html', {'entries': entries, 'quiz_id': quiz_id})



# GLOBAL LEADERBOARD
def leaderboard_list(request):
    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?entry ?player ?score ?quiz WHERE {{
        ?entry a ex:QCM_Leaderboard ;
               ex:playerName ?player ;
               ex:score ?score ;
               ex:forQuiz ?quiz .
    }} ORDER BY DESC(?score)
    """)
    entries = []
    for r in results:
        quiz_iri = r['quiz']['value']
        quiz_id = quiz_iri.split('#')[-1]
        title_res = run_select(f"""
        PREFIX ex: <{EX}>
        SELECT ?title WHERE {{ {iri(quiz_id)} ex:quizTitle ?title }}
        """)
        title = title_res[0]['title']['value'] if title_res else quiz_id
        entries.append({
            'playerName': r['player']['value'],
            'score': r['score']['value'],
            'quizTitle': title
        })
    return render(request, 'quiz/leaderboard.html', {'entries': entries})


# UPDATE QUIZ
def update_quiz(request, quiz_id):
    quiz_iri = iri(quiz_id)
    if request.method == 'POST':
        new_title = request.POST['quizTitle'].strip()
        run_update(f"""
        PREFIX ex: <{EX}>
        DELETE WHERE {{ {quiz_iri} ex:quizTitle ?o }} ;
        INSERT DATA {{ {quiz_iri} ex:quizTitle "{new_title}" }}
        """)
        return redirect('quiz_detail', quiz_id=quiz_id)

    results = run_select(f"""
    PREFIX ex: <{EX}>
    SELECT ?title WHERE {{ {quiz_iri} ex:quizTitle ?title }}
    """)
    if not results:
        return HttpResponseNotFound("Quiz not found")
    return render(request, 'quiz/update_quiz.html', {
        'quiz_id': quiz_id,
        'title': results[0]['title']['value']
    })


# DELETE QUIZ
def delete_quiz(request, quiz_id):
    quiz_iri = iri(quiz_id)
    if request.method == 'POST':
        run_update(f"""
        PREFIX ex: <{EX}>
        DELETE WHERE {{
            {{ {quiz_iri} ?p ?o }} UNION
            {{ ?q ex:hasQuestion {quiz_iri} }} UNION
            {{ ?question ?p ?o . {quiz_iri} ex:hasQuestion ?question }} UNION
            {{ ?c ?p2 ?o2 . ?question ex:hasChoice ?c }}
        }}
        """)
        return redirect('quiz_list')
    return render(request, 'quiz/delete_quiz.html', {'quiz_id': quiz_id})