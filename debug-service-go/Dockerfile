# Build stage
FROM golang:alpine AS builder

WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o main ./...

# Final stage
FROM alpine:3

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .

# Expose port 8080
EXPOSE 8080

# Create a non-root user
USER 10014

# Run the binary
CMD ["/app/main"]
