This module changes workflow of purchase cost distribution
==========================================================

This module depends on *purchase_landed_cost_posting_entries* changes workflow of distributing purchase landed cost.

Main Features:
--------------

* Adding new field *Landed Cost* (landed_cost) on Purchase Order (PO). Use the field to mark a *Purchase Order* is
  required filling landed cost before receiving a *Incoming Shipment*.

* So do new Landed Cost field on Partner form. Use it mark purchasing from this Partner have or not landed cost.
  When changing the Partner field on PO form, the event onchange will activate and change *Landed Cost* field on PO form
  follow *Landed Cost* of selected partner. However, the value of the field is still changeable.

* Changing workflow of Purchase Cost Distribution:
    1. If PO has landed cost, PO's Incoming Shipment will be pending in *Waiting for Landed Cost* state until expense
       cost for it is imported. We have two ways to import landed cost, create *Purchase Cost Distribution* record
       then import this *Incoming Shipment* or filling expense cost in *Landed Cost* tab on Incoming Shipment form.
       The *Incoming Shipment* going to *Ready for Transfer* state, when finished importing landed cost.
    2. System going to automatically distribute landed cost for Purchase Order and update cost, when PO's Incoming
       Shipment received.

* Providing function re-posting to accounting entries for purchase landed cost in case posting for landed cost in
  background fail


New-workflow:
-------------
* When user creates a PO, a check box "Landed Cost" will follow "Landed Cost" of Partner
  (If this shipment is not or required Landed Cost, user can un-tick/tick).

* With this module, we need to key in import expenses after PO confirmed and before receiving.
  Without Landed Cost Distribution, the Incoming Shipment will be pending in status Waiting for Landed Cost.

* Go to Purchase > Landed Cost > Purchase Cost Distribution > Click Create. Select the pickings to which you want to
  calculate landed costs. Select the account journal in which to post the landed costs. Once you select the pickings,
  the product lines will be added automatically in tab "Picking lines". In tab "Expense", key in Import Expenses
   and other expenses. Click "Calculate" to confirm.

* Now the incoming shipment becomes "Ready to Transfer".
  Upon Receiving, system will proceed the following actions:
  - Update Product Qty
  - Create Journal Entries for PO Price
  - Create Journal Entries for Import Expense
  The Import Expenses will be deducted from the Expense account (which was defined in Expense Type ) and transferred to
  the stock valuation account.

To-do:
------


Credits:
========
Nguyen Thi Thanh Tam, Tia (Mrs.) <tamntt@hanelsoft.vn> - Business Analyst
Tran Anh Dung, Alex (Mr.) <dungta2@hanelsoft.vn> - Developer
Do Thi Quang, Quang (Mrs.) <quangdt@hanelsoft.vn> - Tester
Hanelsoft ERP - NPP Team


Contributors:
-------------
Thanks to Hanelsoft company http://hanelsofterp.com/
