from flask import Flask, render_template
import os
def create_app(test_config=None):
    app = Flask(__name__)
    @app.route('/')
    def content():
        if not os.path.exists('output.txt'):
            open('output.txt', 'x')
            with open('output.txt', 'a') as fd:
                fd.write('Keep refreshing till values load')
        with open('output.txt', 'r') as f:
            return render_template('content.html', text=f.read())
    return app
app = create_app()
if __name__ == "__main__":
    app.run(host='0.0.0.0')