package com.rag.app.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

/** Proxie les opérations d'ingestion de cours vers le service Python (rag-service). */
@Service
@Slf4j
public class CourseAdminService {

    private final String ragServiceUrl;
    private final RestTemplate restTemplate;

    public CourseAdminService(@Value("${app.rag-service.url}") String ragServiceUrl) {
        this.ragServiceUrl = ragServiceUrl;
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(30_000);
        this.restTemplate = new RestTemplate(factory);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> uploadCourse(String courseName, MultipartFile file) {
        try {
            var fileResource = new ByteArrayResource(file.getBytes()) {
                @Override public String getFilename() { return file.getOriginalFilename(); }
            };

            var body = new LinkedMultiValueMap<String, Object>();
            body.add("course_name", courseName);
            body.add("file", fileResource);

            var headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            var request = new HttpEntity<>(body, headers);

            var response = restTemplate.postForObject(ragServiceUrl + "/ingest", request, Map.class);
            return (Map<String, Object>) response;
        } catch (IOException e) {
            throw new RuntimeException("Impossible de lire le fichier envoyé.", e);
        } catch (HttpClientErrorException e) {
            throw new IllegalArgumentException(extractError(e));
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getJobStatus(String jobId) {
        try {
            return (Map<String, Object>) (Map<?, ?>) restTemplate.getForObject(
                    ragServiceUrl + "/ingest/" + jobId, Map.class);
        } catch (HttpClientErrorException.NotFound e) {
            throw new com.rag.app.exception.ResourceNotFoundException("Job d'ingestion introuvable.");
        }
    }

    public void deleteCourse(String courseName) {
        try {
            restTemplate.delete(ragServiceUrl + "/courses/" + courseName);
        } catch (HttpClientErrorException e) {
            throw new IllegalArgumentException(extractError(e));
        }
    }

    private String extractError(HttpClientErrorException e) {
        try {
            var body = e.getResponseBodyAs(Map.class);
            if (body != null && body.get("detail") != null) return body.get("detail").toString();
        } catch (Exception ignored) {}
        return "Le service d'ingestion a renvoyé une erreur.";
    }
}
