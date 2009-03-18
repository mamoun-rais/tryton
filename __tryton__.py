#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    "name" : "Account Invoice Line Standalone",
    "name_fr_FR" : "Ligne de facture autonome",
    "version" : "1.1.0",
    "author" : "B2CK",
    'email': 'info@b2ck.com',
    'website': 'http://www.tryton.org/',
    "description": '''Allow to create standalone invoice lines and add them later to a draft
invoice. The invoice will only accept invoice lines with the same
type, company, currency and party.
''',
    "description_fr_FR": '''Permet de créer des lignes de facture autonomes et de les ajouter
ensuite à des factures dans l'état brouillon. La facture n'acceptera
que des lignes qui ont les même type, compagnie, devis et tiers.
''',
    "depends" : [
        "ir",
        "account_invoice",
    ],
    "xml" : [
        "invoice.xml",
    ],
    'translation': [
        'fr_FR.csv',
    ],
}
