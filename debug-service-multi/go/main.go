package main

import (
    "encoding/json"
    "io"
    "log"
    "net/http"
)

func healthzHandler(w http.ResponseWriter, r *http.Request) {
    response := map[string]string{
        "status":  "healthy",
        "service": "golang",
    }
    json.NewEncoder(w).Encode(response)
}

func echoHandler(w http.ResponseWriter, r *http.Request) {
    body, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, "Error reading body", http.StatusBadRequest)
        return
    }

    var data interface{}
    if err := json.Unmarshal(body, &data); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    response := map[string]interface{}{
        "service": "golang",
        "echo":    data,
    }
    json.NewEncoder(w).Encode(response)
}

func main() {
    http.HandleFunc("/healthz", healthzHandler)
    http.HandleFunc("/echo", echoHandler)
    log.Fatal(http.ListenAndServe(":8082", nil))
} 