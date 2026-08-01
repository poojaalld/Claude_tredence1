package com.tredence.digitalbanking.transactions;

import com.tredence.digitalbanking.accounts.Account;
import com.tredence.digitalbanking.accounts.AccountService;
import com.tredence.digitalbanking.common.exception.BadRequestException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class TransactionService {

    private final TransactionRepository transactionRepository;
    private final AccountService accountService;

    @Transactional
    public Transaction deposit(String accountNumber, BigDecimal amount) {
        Account account = accountService.getByAccountNumber(accountNumber);
        accountService.credit(account, amount);

        return transactionRepository.save(Transaction.builder()
                .reference(newReference())
                .type(TransactionType.DEPOSIT)
                .targetAccount(account)
                .amount(amount)
                .createdAt(Instant.now())
                .build());
    }

    @Transactional
    public Transaction withdraw(String accountNumber, BigDecimal amount) {
        Account account = accountService.getByAccountNumber(accountNumber);
        accountService.debit(account, amount);

        return transactionRepository.save(Transaction.builder()
                .reference(newReference())
                .type(TransactionType.WITHDRAWAL)
                .sourceAccount(account)
                .amount(amount)
                .createdAt(Instant.now())
                .build());
    }

    @Transactional
    public Transaction transfer(String sourceAccountNumber, String targetAccountNumber, BigDecimal amount) {
        if (sourceAccountNumber.equals(targetAccountNumber)) {
            throw new BadRequestException("Source and target account must differ");
        }

        Account source = accountService.getByAccountNumber(sourceAccountNumber);
        Account target = accountService.getByAccountNumber(targetAccountNumber);

        accountService.debit(source, amount);
        accountService.credit(target, amount);

        return transactionRepository.save(Transaction.builder()
                .reference(newReference())
                .type(TransactionType.TRANSFER)
                .sourceAccount(source)
                .targetAccount(target)
                .amount(amount)
                .createdAt(Instant.now())
                .build());
    }

    public List<Transaction> getHistory(String accountNumber) {
        return transactionRepository.findAllForAccount(accountNumber);
    }

    private String newReference() {
        return "TXN-" + UUID.randomUUID();
    }
}
