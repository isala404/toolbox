package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"runtime"
	"strconv"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/mem"
)

const (
	htmlContent = `<!DOCTYPE html>
<html>
<body>
<h1>Hello, World!</h1>
</body>
</html>`

	xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<root>
    <message>Hello, World!</message>
</root>`
)

var (
	uploadedFilePath string
	terminating      bool
	upgrader         = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
)

type LogEntry struct {
	Request  RequestDetails  `json:"request"`
	Response ResponseDetails `json:"response"`
}

type RequestDetails struct {
	Method  string            `json:"method"`
	URL     string            `json:"url"`
	Headers map[string]string `json:"headers"`
	Body    interface{}       `json:"body,omitempty"`
}

type ResponseDetails struct {
	Headers    map[string]string `json:"headers"`
	StatusCode int               `json:"status_code"`
	Latency    float64           `json:"latency"`
	ClientIP   string            `json:"client_ip"`
	Body       interface{}       `json:"body,omitempty"`
}

type ProxyRequest struct {
	URL     string                 `json:"url"`
	Method  string                 `json:"method"`
	Payload map[string]interface{} `json:"payload,omitempty"`
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a custom response writer to capture the status code
		rw := &responseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK,
		}

		next.ServeHTTP(rw, r)

		// Create log entry
		logEntry := LogEntry{
			Request: RequestDetails{
				Method:  r.Method,
				URL:     r.URL.String(),
				Headers: convertHeaders(r.Header),
			},
			Response: ResponseDetails{
				Headers:    convertHeaders(w.Header()),
				StatusCode: rw.statusCode,
				Latency:    time.Since(start).Seconds(),
				ClientIP:   r.RemoteAddr,
			},
		}

		// Log as JSON
		logJSON, _ := json.Marshal(logEntry)
		log.Printf("%s", logJSON)
	})
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func convertHeaders(headers http.Header) map[string]string {
	h := make(map[string]string)
	for k, v := range headers {
		if len(v) > 0 {
			h[k] = v[0]
		}
	}
	return h
}

func main() {
	mux := http.NewServeMux()

	// Register all routes
	mux.HandleFunc("/healthz", healthzHandler)
	mux.HandleFunc("/readiness", readinessHandler)
	mux.HandleFunc("/debug", debugHandler)
	mux.HandleFunc("/log", logHandler)
	mux.HandleFunc("/proxy", proxyHandler)
	mux.HandleFunc("/custom-headers", customHeadersHandler)
	mux.HandleFunc("/proxy-http-bin", proxyHTTPBinHandler)
	mux.HandleFunc("/html", htmlHandler)
	mux.HandleFunc("/xml", xmlHandler)
	mux.HandleFunc("/upload", uploadHandler)
	mux.HandleFunc("/download", downloadHandler)
	mux.HandleFunc("/stateless", statelessHandler)
	mux.HandleFunc("/websocket", websocketHandler)
	mux.HandleFunc("/sse", sseHandler)
	mux.HandleFunc("/crash", crashHandler)
	mux.HandleFunc("/shutdown", shutdownHandler)
	mux.HandleFunc("/stress/cpu", stressCPUHandler)
	mux.HandleFunc("/stress/memory", stressMemoryHandler)
	mux.HandleFunc("/reset", resetHandler)

	// Apply middleware
	handler := loggingMiddleware(mux)

	// Create server with timeout configurations
	server := &http.Server{
		Addr:    ":8080",
		Handler: handler,
	}

	// Channel to listen for errors coming from the listener.
	serverErrors := make(chan error, 1)

	// Start the server
	go func() {
		log.Printf("Server listening on %s", server.Addr)
		serverErrors <- server.ListenAndServe()
	}()

	// Channel to listen for an interrupt or terminate signal from the OS.
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)

	// Blocking main and waiting for shutdown.
	select {
	case err := <-serverErrors:
		log.Fatalf("Error starting server: %v", err)

	case sig := <-shutdown:
		log.Printf("main: %v : Start shutdown", sig)
		terminating = true

		// Give outstanding requests a deadline for completion.
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		// Asking listener to shut down and shed load.
		if err := server.Shutdown(ctx); err != nil {
			log.Printf("main : Graceful shutdown did not complete in %v : %v", 5*time.Second, err)
			if err := server.Close(); err != nil {
				log.Printf("main : Could not stop http server: %v", err)
			}
		}
	}
}

func healthzHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"status": "OK"})
}

func readinessHandler(w http.ResponseWriter, r *http.Request) {
	if terminating {
		http.Error(w, "Server is shutting down", http.StatusServiceUnavailable)
		return
	}
	json.NewEncoder(w).Encode(map[string]string{"status": "OK"})
}

func debugHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	seconds := r.URL.Query().Get("seconds")
	if seconds != "" {
		sleepTime, _ := strconv.Atoi(seconds)
		time.Sleep(time.Duration(sleepTime) * time.Second)
	}

	statusCode := r.URL.Query().Get("status_code")
	if statusCode != "" {
		code, _ := strconv.Atoi(statusCode)
		w.WriteHeader(code)
	}

	requestInfo := map[string]interface{}{
		"headers":     r.Header,
		"method":      r.Method,
		"url":         r.URL.String(),
		"remote_addr": r.RemoteAddr,
	}

	json.NewEncoder(w).Encode(requestInfo)
}

func logHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	message := r.URL.Query().Get("message")
	level := r.URL.Query().Get("level")

	switch level {
	case "info":
		log.Printf("[INFO] %s", message)
	case "warning":
		log.Printf("[WARNING] %s", message)
	case "error":
		log.Printf("[ERROR] %s", message)
	default:
		log.Printf("[DEBUG] %s", message)
	}

	json.NewEncoder(w).Encode(map[string]string{
		"message": message,
		"level":   level,
	})
}

func proxyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var proxyReq ProxyRequest
	if err := json.NewDecoder(r.Body).Decode(&proxyReq); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	client := &http.Client{}
	req, err := http.NewRequest(proxyReq.Method, proxyReq.URL, nil)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if proxyReq.Payload != nil {
		payloadBytes, _ := json.Marshal(proxyReq.Payload)
		req.Body = io.NopCloser(bytes.NewBuffer(payloadBytes))
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer resp.Body.Close()

	var responseBody interface{}
	if err := json.NewDecoder(resp.Body).Decode(&responseBody); err != nil {
		// If JSON decoding fails, read the response as plain text
		bodyBytes, _ := io.ReadAll(resp.Body)
		responseBody = string(bodyBytes)
	}

	response := map[string]interface{}{
		"response": map[string]interface{}{
			"headers": resp.Header,
			"body":    responseBody,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func customHeadersHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var headers map[string]string
	if err := json.NewDecoder(r.Body).Decode(&headers); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	for key, value := range headers {
		w.Header().Set(key, value)
	}
}

func proxyHTTPBinHandler(w http.ResponseWriter, r *http.Request) {
	resp, err := http.Get("http://httpbin.org/anything")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	w.Header().Set("Content-Type", "application/json")
	io.Copy(w, resp.Body)
}

func htmlHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, htmlContent)
}

func xmlHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/xml")
	fmt.Fprint(w, xmlContent)
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer file.Close()

	uploadedFilePath = fmt.Sprintf("/tmp/%s", header.Filename)
	out, err := os.Create(uploadedFilePath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer out.Close()

	_, err = io.Copy(out, file)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"filename": header.Filename})
}

func downloadHandler(w http.ResponseWriter, r *http.Request) {
	if uploadedFilePath == "" {
		json.NewEncoder(w).Encode(map[string]string{"message": "No file uploaded"})
		return
	}

	http.ServeFile(w, r, uploadedFilePath)
}

func statelessHandler(w http.ResponseWriter, r *http.Request) {
	seconds := r.URL.Query().Get("seconds")
	if seconds != "" {
		sleepTime, _ := strconv.Atoi(seconds)
		time.Sleep(time.Duration(sleepTime) * time.Second)
	}

	w.Header().Set("Connection", "close")
	json.NewEncoder(w).Encode(map[string]string{"status": "OK"})
}

func websocketHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Websocket upgrade error: %v", err)
		return
	}
	defer conn.Close()

	for {
		messageType, p, err := conn.ReadMessage()
		if err != nil {
			return
		}
		message := fmt.Sprintf("Echo: %s", string(p))
		if err := conn.WriteMessage(messageType, []byte(message)); err != nil {
			return
		}
	}
}

func sseHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "SSE not supported", http.StatusInternalServerError)
		return
	}

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-r.Context().Done():
			return
		case t := <-ticker.C:
			fmt.Fprintf(w, "data: The server time is %s\n\n", t.Format("15:04:05"))
			flusher.Flush()
		}
	}
}

func crashHandler(w http.ResponseWriter, r *http.Request) {
	os.Exit(1)
}

func shutdownHandler(w http.ResponseWriter, r *http.Request) {
	os.Exit(0)
}

func stressCPUHandler(w http.ResponseWriter, r *http.Request) {
	cpuPercent, err := strconv.Atoi(r.URL.Query().Get("cpu_percent"))
	if err != nil || cpuPercent < 0 || cpuPercent > 100 {
		http.Error(w, "CPU percentage must be between 0 and 100", http.StatusBadRequest)
		return
	}

	duration, err := strconv.Atoi(r.URL.Query().Get("duration"))
	if err != nil || duration < 0 {
		http.Error(w, "Duration must be non-negative", http.StatusBadRequest)
		return
	}

	go func() {
		endTime := time.Now().Add(time.Duration(duration) * time.Second)
		for time.Now().Before(endTime) {
			cpuUsage, _ := cpu.Percent(100*time.Millisecond, false)
			if len(cpuUsage) > 0 && cpuUsage[0] < float64(cpuPercent) {
				runtime.GC()
			}
		}
	}()

	json.NewEncoder(w).Encode(map[string]string{
		"message": fmt.Sprintf("CPU stressed at %d%% for %d seconds", cpuPercent, duration),
	})
}

func stressMemoryHandler(w http.ResponseWriter, r *http.Request) {
	memoryPercent, err := strconv.Atoi(r.URL.Query().Get("memory_percent"))
	if err != nil || memoryPercent < 0 || memoryPercent > 100 {
		http.Error(w, "Memory percentage must be between 0 and 100", http.StatusBadRequest)
		return
	}

	duration, err := strconv.Atoi(r.URL.Query().Get("duration"))
	if err != nil || duration < 0 {
		http.Error(w, "Duration must be non-negative", http.StatusBadRequest)
		return
	}

	go func() {
		v, _ := mem.VirtualMemory()
		memoryToUse := v.Total * uint64(memoryPercent) / 100
		data := make([]byte, memoryToUse)
		time.Sleep(time.Duration(duration) * time.Second)
		runtime.KeepAlive(data)
	}()

	json.NewEncoder(w).Encode(map[string]string{
		"message": fmt.Sprintf("Memory stressed at %d%% for %d seconds", memoryPercent, duration),
	})
}

func resetHandler(w http.ResponseWriter, r *http.Request) {
	do, _ := strconv.ParseBool(r.URL.Query().Get("do"))
	if do {
		w.Header().Set("Connection", "close")
		w.Write([]byte("Connection will be reset"))
		return
	}
	json.NewEncoder(w).Encode(map[string]string{"message": "Reset not performed"})
}
