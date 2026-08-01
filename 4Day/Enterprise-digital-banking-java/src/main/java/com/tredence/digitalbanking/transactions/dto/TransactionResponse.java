package com.tredence.digitalbanking.transactions.dto;

import com.tredence.digitalbanking.transactions.Transaction;

import java.math.BigDecimal;
import java.time.Instant;

public record TransactionResponse(
        String reference,
        String type,
        String sourceAccountNumber,
        String targetAccountNumber,
        BigDecimal amount,
        Instant createdAt
) {
    public static TransactionResponse from(Transaction transaction) {
        return new TransactionResponse(
                transaction.getReference(),
                transaction.getType().name(),
                transaction.getSourceAccount() != null ? transaction.getSourceAccount().getAccountNumber() : null,
                transaction.getTargetAccount() != null ? transaction.getTargetAccount().getAccountNumber() : null,
                transaction.getAmount(),
                transaction.getCreatedAt());
    }
}
