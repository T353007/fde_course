package com.northstar.document.ocr;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;

class AmountParserTest {

    @Test
    void parsesPlainNumbers() {
        assertThat(AmountParser.parse("48230.00")).isEqualByComparingTo(new BigDecimal("48230.00"));
    }

    @Test
    void parsesThousandsSeparators() {
        assertThat(AmountParser.parse("48,230.00")).isEqualByComparingTo(new BigDecimal("48230.00"));
    }

    @Test
    void parsesDollarSigns() {
        assertThat(AmountParser.parse("$48,230.00")).isEqualByComparingTo(new BigDecimal("48230.00"));
    }

    @Test
    void parsesEuropeanFormatting() {
        assertThat(AmountParser.parse("48.230,00")).isEqualByComparingTo(new BigDecimal("48230.00"));
    }

    @Test
    void treatsParenthesesAsNegative() {
        assertThat(AmountParser.parse("(8,000.00)")).isEqualByComparingTo(new BigDecimal("-8000.00"));
    }

    @Test
    void handlesLeadingSigns() {
        assertThat(AmountParser.parse("+30000")).isEqualByComparingTo(new BigDecimal("30000"));
        assertThat(AmountParser.parse("-12000")).isEqualByComparingTo(new BigDecimal("-12000"));
    }

    @Test
    void returnsNullForGarbage() {
        assertThat(AmountParser.parse("approximately 78,231")).isNull();
        assertThat(AmountParser.parse("")).isNull();
        assertThat(AmountParser.parse(null)).isNull();
    }
}
