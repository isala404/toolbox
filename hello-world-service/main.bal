import ballerina/http;

type Greeting record {
    string 'from;
    string message;
};

service / on new http:Listener(8080) {
    resource function get .() returns Greeting {
        Greeting greetingMessage = {"from" : "Choreo", "message" : "Hello World!"};
        return greetingMessage;
    }
}