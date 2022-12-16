# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from . import account
from . import configuration
from . import company
from . import fiscalyear
from . import journal
from . import move
from . import move_template
from . import party
from . import period
from . import tax

from .move import MoveLineMixin

__all__ = ['register', 'MoveLineMixin']


def register():
    Pool.register(
        fiscalyear.FiscalYear,
        fiscalyear.BalanceNonDeferralStart,
        company.Company,
        account.TypeTemplate,
        account.Type,
        account.AccountTemplate,
        account.AccountTemplateTaxTemplate,
        account.Account,
        account.AccountParty,
        account.AccountDeferral,
        account.AccountTax,
        account.OpenChartAccountStart,
        account.GeneralLedgerAccount,
        account.GeneralLedgerAccountContext,
        account.GeneralLedgerAccountParty,
        account.GeneralLedgerLine,
        account.GeneralLedgerLineContext,
        account.BalanceSheetContext,
        account.BalanceSheetComparisionContext,
        account.IncomeStatementContext,
        account.CreateChartStart,
        account.CreateChartAccount,
        account.CreateChartProperties,
        account.UpdateChartStart,
        account.UpdateChartSucceed,
        account.AgedBalanceContext,
        account.AgedBalance,
        configuration.Configuration,
        configuration.ConfigurationDefaultAccount,
        configuration.DefaultTaxRule,
        configuration.Sequence,
        period.Period,
        journal.Journal,
        journal.JournalSequence,
        journal.JournalCashContext,
        journal.JournalPeriod,
        move.Move,
        move.Reconciliation,
        configuration.ConfigurationTaxRounding,
        move.Line,
        move.WriteOff,
        move.OpenJournalAsk,
        move.ReconcileLinesWriteOff,
        move.ReconcileShow,
        move.CancelMovesDefault,
        move.GroupLinesStart,
        move.SplitLinesStart,
        move.SplitLinesPreview,
        move.SplitLinesTerm,
        tax.TaxGroup,
        tax.TaxCodeTemplate,
        tax.TaxCode,
        tax.TaxCodeLineTemplate,
        tax.TaxCodeLine,
        tax.OpenChartTaxCodeStart,
        tax.TaxTemplate,
        tax.Tax,
        tax.TaxLine,
        tax.TaxRuleTemplate,
        tax.TaxRule,
        tax.TaxRuleLineTemplate,
        tax.TaxRuleLine,
        tax.TestTaxView,
        tax.TestTaxViewResult,
        move_template.MoveTemplate,
        move_template.MoveTemplateKeyword,
        move_template.MoveLineTemplate,
        move_template.TaxLineTemplate,
        move_template.CreateMoveTemplate,
        move_template.CreateMoveKeywords,
        party.Party,
        party.PartyAccount,
        fiscalyear.CreatePeriodsStart,
        fiscalyear.RenewFiscalYearStart,
        module='account', type_='model')
    Pool.register(
        account.OpenType,
        fiscalyear.BalanceNonDeferral,
        account.OpenChartAccount,
        account.CreateChart,
        account.UpdateChart,
        account.OpenGeneralLedgerAccountParty,
        move.OpenJournal,
        move.OpenAccount,
        move.ReconcileLines,
        move.UnreconcileLines,
        move.Reconcile,
        move.CancelMoves,
        move.GroupLines,
        move.SplitLines,
        move_template.CreateMove,
        tax.OpenChartTaxCode,
        tax.OpenTaxCode,
        tax.TestTax,
        party.PartyReplace,
        party.PartyErase,
        fiscalyear.CreatePeriods,
        fiscalyear.RenewFiscalYear,
        module='account', type_='wizard')
    Pool.register(
        account.AccountTypeStatement,
        account.GeneralLedger,
        account.TrialBalance,
        account.AgedBalanceReport,
        move.GeneralJournal,
        module='account', type_='report')
