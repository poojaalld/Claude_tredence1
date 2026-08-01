package com.tredence.digitalbanking.transactions;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface TransactionRepository extends JpaRepository<Transaction, Long> {

    Optional<Transaction> findByReference(String reference);

    @Query("select t from Transaction t "
            + "where t.sourceAccount.accountNumber = :accountNumber "
            + "or t.targetAccount.accountNumber = :accountNumber "
            + "order by t.createdAt desc")
    List<Transaction> findAllForAccount(@Param("accountNumber") String accountNumber);
}
