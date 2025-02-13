package com.debug;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@SpringBootApplication
@RestController
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @GetMapping("/healthz")
    public Map<String, String> healthCheck() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "healthy");
        response.put("service", "java");
        return response;
    }

    @PostMapping("/echo")
    public Map<String, Object> echo(@RequestBody Object body) {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "java");
        response.put("echo", body);
        return response;
    }
} 
