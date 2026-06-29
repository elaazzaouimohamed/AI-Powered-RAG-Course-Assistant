package com.rag.app.config;

import com.rag.app.model.*;
import com.rag.app.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepo;
    private final LlmConfigRepository llmRepo;
    private final PasswordEncoder encoder;

    @Override
    public void run(String... args) {
        seedAdminUser();
        seedLlmConfigs();
    }

    private void seedAdminUser() {
        if (!userRepo.existsByUsername("admin")) {
            userRepo.save(User.builder()
                    .username("admin")
                    .email("admin@rag.local")
                    .password(encoder.encode("admin123"))
                    .role(Role.ADMIN)
                    .active(true)
                    .build());
            log.info("Admin user created — username: admin / password: admin123");
        }
        if (!userRepo.existsByUsername("demo")) {
            userRepo.save(User.builder()
                    .username("demo")
                    .email("demo@rag.local")
                    .password(encoder.encode("demo123"))
                    .role(Role.USER)
                    .active(true)
                    .build());
            log.info("Demo user created — username: demo / password: demo123");
        }
    }

    private void seedLlmConfigs() {
        if (llmRepo.count() == 0) {
            llmRepo.save(LlmConfig.builder()
                    .name("LM Studio — gemma-3-4b-it (Recommandé)")
                    .backend("lmstudio")
                    .model("gemma-3-4b-it")
                    .baseUrl("http://localhost:1234/v1")
                    .enabled(true)
                    .isDefault(true)
                    .build());
            llmRepo.save(LlmConfig.builder()
                    .name("Ollama — gemma3:4b (CPU)")
                    .backend("ollama")
                    .model("gemma3:4b")
                    .baseUrl("http://localhost:11434")
                    .enabled(true)
                    .isDefault(false)
                    .build());
            llmRepo.save(LlmConfig.builder()
                    .name("Ollama — phi3:mini (Rapide)")
                    .backend("ollama")
                    .model("phi3:mini")
                    .baseUrl("http://localhost:11434")
                    .enabled(true)
                    .isDefault(false)
                    .build());
            llmRepo.save(LlmConfig.builder()
                    .name("NVIDIA — Kimi K2.6 (Cloud)")
                    .backend("nvidia")
                    .model("moonshotai/kimi-k2.6")
                    .enabled(true)
                    .isDefault(false)
                    .build());
            log.info("Default LLM configs seeded");
        }
    }
}
