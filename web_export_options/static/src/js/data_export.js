/**
 * Created by trananhdung on 09/11/2016.
 */
openerp.web_export_options = function (instance) {
    instance.web.DataExport = instance.web.DataExport.extend({
        on_click_export_data: function () {
            var self = this;
            var exported_fields = this.$el.find('#fields_list option').map(function () {
                // DOM property is textContent, but IE8 only knows innerText
                return {
                    name: self.records[this.value] || this.value,
                    label: this.textContent || this.innerText
                };
            }).get();

            if (_.isEmpty(exported_fields)) {
                alert(_t("Please select fields to export..."));
                return;
            }
            exported_fields.unshift({name: 'id', label: 'External ID'});

            var export_format = this.$el.find("#export_format").val();
            var c = instance.webclient.crashmanager;
            var import_compat = this.$el.find("#import_compat").val();
            instance.web.blockUI();
            this.session.get_file({
                url: '/web/export/' + export_format,
                data: {
                    data: JSON.stringify({
                        model: this.dataset.model,
                        fields: exported_fields,
                        ids: this.ids_to_export,
                        domain: this.domain,
                        context: this.dataset.context,
                        import_compat: import_compat
                    })
                },
                complete: instance.web.unblockUI,
                error: c.rpc_error.bind(c)
            });
        }
    });
};