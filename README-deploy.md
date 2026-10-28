# Deploying to IBM Cloud Code Engine

## 1. Prerequisites

- [IBM Cloud CLI](https://cloud.ibm.com/docs/cli) (`ibmcloud login`)
- Code Engine plugin:
  ```
  ibmcloud plugin install code-engine
  ```
- Docker (or Podman)
- Access to a container registry (IBM Cloud Container Registry or Docker Hub)
- A Code Engine project selected: `ibmcloud ce project select --name <project>`

## 2. Local development

Run the backend and the frontend dev server together in two terminals.

```
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
CLIENT_ID=xxx CLIENT_SECRET=yyy MANDATORY_METADATA='["businessOwners","Inputs","Outputs"]' uvicorn backend.main:app --reload

# Terminal 2 — frontend dev server (proxies /api to localhost:8000)
cd frontend
npm run dev
```

Note: `backend.main:app` is resolved relative to the repository root, so run the `uvicorn` command from the repo root (e.g. `uvicorn backend.main:app --reload`) if the import fails from inside `backend/`.

On Windows PowerShell, set the variables first:

```
$env:CLIENT_ID="xxx"; $env:CLIENT_SECRET="yyy"; $env:MANDATORY_METADATA='["businessOwners","Inputs","Outputs"]'
```

## 3. Build and push the container image

```
docker build -t us.icr.io/<namespace>/blueworksapi:latest .
docker push us.icr.io/<namespace>/blueworksapi:latest
```

The Dockerfile builds the React SPA (`npm ci && npm run build`) and copies `frontend/dist` into `backend/static/`, which FastAPI serves from `/`.

## 4. Create Code Engine secrets

```
ibmcloud ce secret create --name blueworks-secrets \
  --from-literal CLIENT_ID=<your-client-id> \
  --from-literal CLIENT_SECRET=<your-client-secret> \
  --from-literal "MANDATORY_METADATA=[\"businessOwners\",\"Inputs\",\"Outputs\"]"
```

If the registry is private, also create a registry secret and pass `--registry-secret <name>` when deploying.

## 5. Deploy the application

```
ibmcloud ce application create \
  --name blueworksapi \
  --image us.icr.io/<namespace>/blueworksapi:latest \
  --port 8080 \
  --env-from-secret blueworks-secrets \
  --min-scale 0 \
  --max-scale 3
```

## 6. Update an existing deployment

```
ibmcloud ce application update \
  --name blueworksapi \
  --image us.icr.io/<namespace>/blueworksapi:latest
```

## 7. Get the application URL

```
ibmcloud ce application get --name blueworksapi --output url
```
