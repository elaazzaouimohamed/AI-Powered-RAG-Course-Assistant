package com.rag.app.dto.auth;

import jakarta.validation.constraints.*;
import lombok.Data;

@Data
public class RegisterRequest {
    @NotBlank @Size(min = 3, max = 30) private String username;
    @NotBlank @Email                    private String email;
    @NotBlank @Size(min = 6)            private String password;
}
