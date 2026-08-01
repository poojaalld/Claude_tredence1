package com.tredence.digitalbanking.auth.dto;

public record AuthResponse(
        String token,
        String email,
        String fullName,
        String role
) {
}
