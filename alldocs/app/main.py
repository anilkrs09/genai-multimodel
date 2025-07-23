# app/main.py
from flask import Flask, request, render_template
from query import query_chunks_with_ollama

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        question = request.form.get("question")
        result = query_chunks_with_ollama(question)
        return render_template("result.html", result=result)
    return '''
        <form method="post">
            <label>Ask a question:</label><br>
            <textarea name="question" rows="4" cols="50"></textarea><br>
            <button type="submit">Submit</button>
        </form>
    '''

if __name__ == "__main__":
    app.run(debug=True)

