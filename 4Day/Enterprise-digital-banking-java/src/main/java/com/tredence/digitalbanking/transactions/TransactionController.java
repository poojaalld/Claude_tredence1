package com.tredence.digitalbanking.transactions;

import com.tredence.digitalbanking.transactions.dto.DepositRequest;
import com.tredence.digitalbanking.transactions.dto.TransactionResponse;
import com.tredence.digitalbanking.transactions.dto.TransferRequest;
import com.tredence.digitalbanking.transactions.dto.WithdrawRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/transactions")
@RequiredArgsConstructor
public class TransactionController {

    private final TransactionService transactionService;

    @PostMapping("/deposit")
    public ResponseEntity<TransactionResponse> deposit(@Valid @RequestBody DepositRequest request) {
        Transaction transaction = transactionService.deposit(request.accountNumber(), request.amount());
        return ResponseEntity.ok(TransactionResponse.from(transaction));
    }

    @PostMapping("/withdraw")
    public ResponseEntity<TransactionResponse> withdraw(@Valid @RequestBody WithdrawRequest request) {
        Transaction transaction = transactionService.withdraw(request.accountNumber(), request.amount());
        return ResponseEntity.ok(TransactionResponse.from(transaction));
    }

    @PostMapping("/transfer")
    public ResponseEntity<TransactionResponse> transfer(@Valid @RequestBody TransferRequest request) {
        Transaction transaction = transactionService.transfer(
                request.sourceAccountNumber(), request.targetAccountNumber(), request.amount());
        return ResponseEntity.ok(TransactionResponse.from(transaction));
    }

    @GetMapping("/account/{accountNumber}")
    public ResponseEntity<List<TransactionResponse>> history(@PathVariable String accountNumber) {
        List<TransactionResponse> history = transactionService.getHistory(accountNumber).stream()
                .map(TransactionResponse::from)
                .toList();
        return ResponseEntity.ok(history);
    }
}
