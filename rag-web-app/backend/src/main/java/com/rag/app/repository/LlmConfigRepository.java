package com.rag.app.repository;

import com.rag.app.model.LlmConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface LlmConfigRepository extends JpaRepository<LlmConfig, Long> {
    List<LlmConfig> findByEnabledTrue();
    List<LlmConfig> findByEnabledTrueOrderByIsDefaultDesc();
    List<LlmConfig> findByIsDefaultTrue();
    Optional<LlmConfig> findFirstByBackendAndModel(String backend, String model);
    Optional<LlmConfig> findFirstByBackendAndEnabledTrue(String backend);
}
