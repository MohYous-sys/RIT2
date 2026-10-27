# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:


## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.

# ReliefOps

## Backend development

Create and activate a virtual environment, then install the backend dependencies:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
```

Run the Flask development server with `python backend/app.py` or `npm run api`. The database schemas, including `requests.db`, are created automatically. In development, the app creates a persistent local Flask secret if `FLASK_SECRET_KEY` is not set.

Run backend tests from the repository root:

```sh
python -m unittest discover -s backend -p 'test_*.py' -v
```

## Production

Use Gunicorn instead of Flask's development server. Set `APP_ENV=production`, provide a stable `FLASK_SECRET_KEY`, and point `DATABASE_DIR` at a writable persistent volume. The app requires the explicit secret in production, disables debug mode, and marks session cookies secure.

```sh
export APP_ENV=production
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export DATABASE_DIR=/var/lib/reliefops
export PORT=8000
.venv/bin/gunicorn --chdir backend --workers 2 --bind "0.0.0.0:${PORT}" app:app
```

Keep the same secret across restarts and instances. Ensure the `DATABASE_DIR` volume is backed up. Terminate HTTPS at the application gateway and serve the frontend and API on the same site; cross-origin API access is not configured.
