
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import os
import tempfile

from app.extractor import extract_sailors_and_events
from app.generator import generate_pg13_zip   # you already have this, or will
from app.config import SECRET_KEY            # put some string there


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates_web")
    )
    app.config["SECRET_KEY"] = SECRET_KEY or "change-me"

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            file = request.files.get("pdf_file")
            if not file:
                flash("Please upload a SEA DUTY CERTIFICATION SHEET PDF.")
                return redirect(url_for("index"))

            # Save uploaded PDF to a temp file
            tmp_dir = tempfile.mkdtemp()
            pdf_path = os.path.join(tmp_dir, file.filename)
            file.save(pdf_path)

            # Extract sailors and events
            sailors = extract_sailors_and_events(pdf_path)
            if not sailors:
                flash("No valid sailors/events found. Check the PDF format.")
                return redirect(url_for("index"))

            # For now, handle first sailor only
            sailor = sailors[0]

            # Generate PG-13 ZIP (you implement this inside generator.py)
            zip_path = generate_pg13_zip(sailor, output_dir=tmp_dir)

            return send_file(
                zip_path,
                as_attachment=True,
                download_name=os.path.basename(zip_path)
            )

        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    # Listen on all interfaces for Docker
    app.run(host="0.0.0.0", port=8080)
