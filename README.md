# ShipFast GitOps – Status API

A small Flask API for ShipFast Logistics, packaged with Docker and deployed to
Kubernetes (kind) through **Argo CD** using GitOps. With GitOps, the Git repo
holds the desired state and Argo CD keeps the cluster matching it.

## Project layout

```
shipfast-gitops/
├── app/
│   ├── app.py               # Flask API: /status and /health
│   └── test_app.py          # pytest tests
├── manifests/               # what Argo CD deploys
│   ├── 00-namespace.yaml    # Namespace "shipfast"
│   ├── 01-configmap.yaml    # APP_ENV setting
│   ├── 02-deployment.yaml   # 2 replicas, probes, resource limits
│   └── 03-service.yaml      # ClusterIP Service on port 5000
├── argocd/
│   └── application.yaml     # Argo CD Application (kept OUTSIDE manifests/)
├── scripts/
│   └── check-placeholders.sh
├── Dockerfile               # multi-stage, slim, non-root, HEALTHCHECK
├── requirements.txt
├── .dockerignore
└── .gitignore
```

## Endpoints

| Endpoint  | Purpose                                                   |
|-----------|-----------------------------------------------------------|
| `/status` | Service name, version, environment, pod hostname, time     |
| `/health` | Returns `{"status": "healthy"}`, used by probes and Docker |

## Step 1: Replace the placeholders

| Placeholder            | File                          | Replace with              |
|------------------------|-------------------------------|---------------------------|
| ~~`<DOCKERHUB_USERNAME>`~~ | `manifests/02-deployment.yaml` | ✅ Done: `dareenzere` |
| ~~`<GITHUB_USERNAME>`~~ | `argocd/application.yaml` | ✅ Done: `Dareen679` |

Then confirm that none are left:

```bash
./scripts/check-placeholders.sh
```

Never push or apply while placeholders remain; Kubernetes and Argo CD cannot use them.

## Step 2: Run and test locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
python -m pytest app/ -v
python app/app.py           # then: curl localhost:5000/status
```

## Step 3: Build and test the Docker image

```bash
docker build -t dareenzere/shipfast-status-api:1.0.0 .
docker run --rm -d -p 5000:5000 --name shipfast-test dareenzere/shipfast-status-api:1.0.0
curl localhost:5000/health
docker inspect --format '{{.State.Health.Status}}' shipfast-test   # healthy after ~30s
docker exec shipfast-test whoami                                    # should NOT be root
docker stop shipfast-test
```

## Step 4: Push the image and the repo

```bash
docker login
docker push dareenzere/shipfast-status-api:1.0.0

git init -b main
git add . && git commit -m "ShipFast status API with GitOps manifests"
git remote add origin https://github.com/Dareen679/shipfast-gitops.git
git push -u origin main
```

The GitHub repo must be **public**, because Argo CD has no credentials configured.

## Step 5: Install Argo CD and deploy

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deploy/argocd-server

kubectl apply -f argocd/application.yaml
kubectl -n argocd get applications          # expect Synced / Healthy
kubectl -n shipfast get pods,svc
```

## Step 6: Verify the running app

```bash
kubectl -n shipfast port-forward svc/shipfast-status-api 5000:5000
curl localhost:5000/status    # run several times; "hostname" changes between the 2 pods
```

## Step 7: Watch GitOps work

- **Self-heal:** run `kubectl -n shipfast scale deploy/shipfast-status-api --replicas=5`. Argo CD scales it back to 2.
- **Change through Git:** edit `APP_ENV` in the ConfigMap, then commit and push. Argo CD syncs the change, usually within 3 minutes.
- **Prune:** delete a manifest from Git and push. Argo CD removes that resource from the cluster.

## Argo CD UI

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
# open https://localhost:8080  (user: admin)
```

## Security notes

- Multi-stage build, so build tools are not included in the final image.
- The app runs as non-root UID 10001, with a read-only root filesystem and all Linux capabilities dropped.
- No service-account token is mounted, because the app never calls the Kubernetes API.
- The image uses a fixed version tag (`1.0.0`) rather than `latest`, so deployments are repeatable.
