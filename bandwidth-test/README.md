# Kubernetes Pod Bandwidth Tester

This FastAPI application allows you to test the ingress (download) and egress (upload) bandwidth of the Kubernetes pod it's running in.

It uses `speedtest-cli` to perform the tests.

## Endpoints

- `GET /test-ingress`: Returns the download speed in Mbps.
- `GET /test-egress`: Returns the upload speed in Mbps.
- `GET /test-all`: Returns download speed (Mbps), upload speed (Mbps), and ping (ms).

## Prerequisites

- Docker
- kubectl (if deploying to Kubernetes)

## How to Build and Run Locally

1.  **Navigate to the `bandwidth-test` directory:**
    ```bash
    cd bandwidth-test
    ```

2.  **Build the Docker image:**
    ```bash
    docker build -t bandwidth-tester .
    ```

3.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 bandwidth-tester
    ```

4.  **Test the endpoints:**
    Open your browser or use `curl`:
    - `curl http://localhost:8000/test-ingress`
    - `curl http://localhost:8000/test-egress`
    - `curl http://localhost:8000/test-all`

## How to Deploy to Kubernetes (Example)

1.  **Push the Docker image to a container registry** (e.g., Docker Hub, GCR, ECR).
    ```bash
    docker tag bandwidth-tester <your-registry>/bandwidth-tester:latest
    docker push <your-registry>/bandwidth-tester:latest
    ```

2.  **Create a Kubernetes Deployment and Service.** Here's a basic example (`bandwidth-test-k8s.yaml`):

    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: bandwidth-tester
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: bandwidth-tester
      template:
        metadata:
          labels:
            app: bandwidth-tester
        spec:
          containers:
          - name: bandwidth-tester
            image: <your-registry>/bandwidth-tester:latest # Replace with your image
            ports:
            - containerPort: 8000
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: bandwidth-tester-svc
    spec:
      selector:
        app: bandwidth-tester
      ports:
        - protocol: TCP
          port: 80
          targetPort: 8000
      # type: LoadBalancer # Uncomment for external access if needed, or use port-forwarding
    ```

3.  **Apply the Kubernetes manifest:**
    ```bash
    kubectl apply -f bandwidth-test-k8s.yaml
    ```

4.  **Test the bandwidth from within the cluster or by port-forwarding:**

    *   **Using Port-Forwarding (for local testing):**
        ```bash
        kubectl port-forward svc/bandwidth-tester-svc 8080:80
        ```
        Then access via `curl http://localhost:8080/test-all`

    *   **From another pod in the cluster:**
        You can `exec` into another pod and `curl` the service name:
        ```bash
        kubectl exec -it <another-pod-name> -- /bin/sh
        # Inside the other pod's shell
        apk add curl # If curl is not installed
        curl http://bandwidth-tester-svc/test-all
        ```

## Notes

- The accuracy of `speedtest-cli` can be influenced by many factors, including the chosen test server and network conditions.
- When running in Kubernetes, the pod's network interface, CNI plugin, and underlying node network will affect the results.
- This tool measures the bandwidth from the perspective of the pod where it is running. 
