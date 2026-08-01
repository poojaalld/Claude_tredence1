package com.tredence.digitalbanking.accounts.dto;

import com.tredence.digitalbanking.accounts.AccountType;
import jakarta.validation.constraints.NotNull;

public record CreateAccountRequest(
        @NotNull AccountType accountType
) {
}
