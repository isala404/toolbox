# Step 1: Build the application
FROM rust:latest as builder

# Create a new empty shell project
RUN USER=root cargo new --bin load-test
WORKDIR /load-test

# Copy the source code
COPY ./Cargo.toml ./Cargo.toml
COPY ./src ./src

# Build the application
RUN cargo build --release

# Step 2: Create the final image
FROM debian:latest

# Install necessary dependencies
RUN apt-get update && apt-get install -y libc6

# Copy the build artifact from the builder stage
COPY --from=builder /load-test/target/release/load-test /usr/local/bin/load-test

# Create a non-root user
USER 10014

# Set the startup command to run the binary
CMD ["load-test"]
