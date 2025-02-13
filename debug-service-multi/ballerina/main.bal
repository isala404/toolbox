import ballerina/http;

service http:Service / on new http:Listener(8084) {
    resource function get healthz() returns json {
        return {
            status: "healthy",
            'service: "ballerina"
        };
    }

    resource function post echo(@http:Payload json payload) returns json {
        return {
            'service: "ballerina",
            echo: payload
        };
    }
} 
