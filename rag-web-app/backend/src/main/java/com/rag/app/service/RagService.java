package com.rag.app.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class RagService {

    private final String ragServiceUrl;
    private final RestTemplate restTemplate;

    public RagService(@Value("${app.rag-service.url}") String ragServiceUrl) {
        this.ragServiceUrl = ragServiceUrl;
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(30_000);
        this.restTemplate = new RestTemplate(factory);
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, String>> retrieveContexts(String question, String course) {
        try {
            var request = Map.of("question", question, "course", course);
            var response = restTemplate.postForObject(
                    ragServiceUrl + "/retrieve", request, Map.class);
            if (response != null && response.containsKey("contexts")) {
                return (List<Map<String, String>>) response.get("contexts");
            }
        } catch (Exception e) {
            log.warn("RAG service unavailable: {}. Continuing without context.", e.getMessage());
        }
        return List.of();
    }

    public List<String> listCourses() {
        try {
            var response = restTemplate.getForObject(ragServiceUrl + "/courses", Map.class);
            if (response != null && response.containsKey("courses")) {
                return (List<String>) response.get("courses");
            }
        } catch (Exception e) {
            log.warn("Could not list courses from RAG service: {}", e.getMessage());
        }
        return List.of("Statistique_cours", "4-kmeans");
    }
}
