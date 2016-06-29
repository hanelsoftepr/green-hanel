This module automatically make stock operations to resolve incomplete production
================================================================================
This module improve managed function of Manufacturing module.


Main features:
--------------
1. Allow automatically creating internal transfers to resolve shortage of raw material
   when check availability before producing. System will check for all locations to looking for
   available raw material follow removal strategy of stock configuration.
   You can set up on *Settings > Configurations > Manufacturing > Automatically resolving by Internal Transfers*
2. If Raw Material is not enough in all Locations, systems automatically create Procurement Order for Items to consume,
   that mean either make manufacturing order or purchase order follow options on Items to consume.
   Setting up by *Settings > Configurations > Manufacturing > Automatically resolving by Procurement Order*

* Note: Option (2) is available only when (1) is enable.

3. Making button "Stock Operation" on Manufacturing Order form to view to Internal Transfers of the Production.
   You should install module *mrp_stock_quant_shortcut* to show quantity onhand of raw material on each locations.

To-do:
------


Author:
=======
HanelsoftERP - NPP Team - http://hanelsofterp.com/page/phan-mem-quan-ly-va-hoach-dinh-san-xuat

Credits:
--------
Nguyen Thi Thanh Tam, Tia <tamntt@hanelsoft.vn> - Business Analyst.
Tran Anh Dung, Alex <dungta2@hanelsoft.vn> - Developer.
Do Thi Quang, Quang <quangdt@hanelsoft.vn> - Tester.

Contributors:
-------------
Thanks to HanelsoftERP - website: http://hanelsofterp.com