This module manages your purchase expenses
==========================================
The functionality of this module is extended from *purchase_landed_cost* of Odoo MRP Team
to additionally provide a way to post to Journal Entries

Main features:
--------------
* Adding *amount_total* field to show total of expense amount
* Defaulting Account Journal on Purchase Cost Distribution form to use in posting Journal Entries
* Adding a expense type to compute by percentage.
* Editing *_calculate_cost* function for each Picking Lines become more exactly
* Posting expense amount to Journal Entries
* Providing 2 way to post JE in Settings > Configurations > Purchases > Cost Distribution, run in current transaction
  or run in background if there are so many Accounting Entries need to post.

Configurations:
---------------
* Purchase Expense Type with calculate method is Percentage by PO line:
  On master form of Purchase Expense Type, choosing *Percentage by PO line*
  on *Calculate Method* field
* Default Journal: On master form of Journals, tick on <b>Default for Cost Distributions</b>.
  Tick on *Use for Cost Distributions* to restrict Journal can choose in PCD form
* Processed way to posting Journal Entries for PCD: *Settings > Configurations > Purchases*,
  tick on Run Cost Distribution in Background to run posting process in background,
  un-tick if you prefer posting process run in current transaction

To-do:
------
* Ability to add expenses in multi currency.
* Costing method (currently is average) for updating product's standard cost
  need to additionally cover *real* and *standard*
* Purchase distribution report.


Credits
=======
Nguyen Thi Thanh Tam, Tia (Mrs.) <tamntt@hanelsoft.vn> - Business Analyst
Tran Anh Dung, Alex (Mr.) <dungta2@hanelsoft.vn> - Developer
Hanelsoft ERP - NPP Team

Contributors:
-------------
Thanks to Hanelsoft company http://hanelsofterp.com/
