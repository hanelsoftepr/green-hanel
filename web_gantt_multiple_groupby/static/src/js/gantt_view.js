/**
 * Created by trananhdung on 05/08/2016.
 */

openerp.web_gantt_multiple_groupby = function (instance) {
    var QWeb = instance.web.qweb;

    instance.web_gantt.GanttView.include({

        do_search: function (domains, contexts, group_bys) {
            var self = this;
            self.last_domains = domains;
            self.last_contexts = contexts;
            self.last_group_bys = group_bys;
            // select the group by
            var n_group_bys = [];
            if (this.fields_view.arch.attrs.default_group_by) {
                n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
            }
            if (group_bys.length) {
                n_group_bys = group_bys;
            }
            // gather the fields to get
            var fields = _.compact(_.map(["date_start", "date_delay", "date_stop", "progress"], function (key) {
                return self.fields_view.arch.attrs[key] || '';
            }));
            fields = _.uniq(fields.concat(n_group_bys));
            var l = [];
            _.each(self.fields_view.fields, function (value, key) {
                fields = fields.concat([key]);
            });
            fields = _.uniq(fields);

            return $.when(this.has_been_loaded).then(function () {
                return self.dataset.read_slice(fields, {
                    domain: domains,
                    context: contexts
                }).then(function (data) {
                    return self.on_data_loaded(data, n_group_bys);
                });
            });
        },

        get_progress_rate: function (groups, plevel) {
            var self = this;
            var progress_rate = 0.00;
            var len = groups.length;
            var level = plevel || 0;
            _.each(groups, function (group, index, groups) {
                if (group.__is_group) {
                    var _progress_rate = self.get_progress_rate(group.tasks, level + 1);
                    if (level > 0) {
                        group.progress_rate = _progress_rate;
                    }
                }
                progress_rate += group.progress_rate / len;
            });
            return progress_rate;
        },

        split_child_groups: function (groups, group_by) {
            //var tmp_groups = [];
            var self = this;
            for (var i = 0; i < groups.length; i++) {

                var tmp_task = groups[i].tasks;
                if (groups[i].__is_group) {
                    groups[i].tasks = self.split_child_groups(tmp_task, group_by);
                }
                else {
                    return self.split_groups(groups, [group_by]);
                }
            }
            return groups;
        },

        split_groups: function (tasks, group_bys) {
            var self = this;
            if (group_bys.length === 0)
                return tasks;
            if (group_bys.length > 1) {
                var groups = self.split_groups(tasks, group_bys.slice(0, group_bys.length - 1));
                groups = self.split_child_groups(groups, group_bys[group_bys.length - 1]);
                return groups;
            }
            else {
                var groups = [];
                tasks.forEach = undefined;
                _.each(tasks, function (task) {
                    var self = this;
                    var group_name = task[_.first(group_bys)];
                    var group = _.find(groups, function (group) {
                        return _.isEqual(group.name, group_name);
                    });
                    if (group === undefined) {
                        var _comment = self.fields_to_string(task);
                        group = {name: group_name, tasks: [], __is_group: true, comment: _comment};
                        groups.push(group);
                    }
                    group.tasks.push(task);
                }, self);
                _.each(groups, function (group) {
                    group.tasks = self.split_groups(group.tasks, _.rest(group_bys));
                });
                return groups;
            }
        },

        fields_to_string: function(obj){
            var self = this;
            var arch_fields = self.fields_view.arch.children;
            var fields = self.fields_view.fields;
            var string_result = "";
            //fields.forEach = undefined;
            _.each(arch_fields, function(field){
                string_result += this.instance.web.format_value(
                        obj[field.attrs.name],
                        this.fields[field.attrs.name]
                    ) + " ";
            }, {instance: instance, fields: fields});
            return string_result.substr(0, string_result.length - 1);
        },

        on_data_loaded_2: function (tasks, group_bys) {
            var self = this;
            $(".oe_gantt", this.$el).html("");

            // No prevent multi group
            if (group_bys.length == 0) {
                group_bys = ["_pseudo_group_by"];
                _.each(tasks, function (el) {
                    el._pseudo_group_by = "Gantt View";
                });
                this.fields._pseudo_group_by = {type: "string"};
            }
            var groups = self.split_groups(tasks, group_bys);
            self.get_progress_rate(groups);

            // track ids of task items for context menu
            var task_ids = {};
            // creation of the chart
            var generate_task_info = function (task, plevel) {
                if (_.isNumber(task[self.fields_view.arch.attrs.progress])) {
                    var percent = task[self.fields_view.arch.attrs.progress] || 0;
                } else {
                    var percent = 100;
                }
                var level = plevel || 0;
                if (task.__is_group) {
                    var task_infos = _.compact(_.map(task.tasks, function (sub_task) {
                        return generate_task_info(sub_task, level + 1);
                    }));
                    if (task_infos.length == 0)
                        return;
                    var task_start = _.reduce(_.pluck(task_infos, "task_start"), function (date, memo) {
                        return memo === undefined || date < memo ? date : memo;
                    }, undefined);
                    var task_stop = _.reduce(_.pluck(task_infos, "task_stop"), function (date, memo) {
                        return memo === undefined || date > memo ? date : memo;
                    }, undefined);

                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    // Default working time is 8 hours per day => duration
                    duration = duration / 3;
                    var group_name = task.name ? instance.web.format_value(task.name, self.fields[group_bys[level]]) : "-";
                    if (level == 0) {
                        var group = new GanttProjectInfo(_.uniqueId("gantt_project_"), group_name, task_start);
                        _.each(task_infos, function (el) {
                            group.addTask(el.task_info);
                        });
                        return group;
                    } else {
                        //var group = new GanttTaskInfo(_.uniqueId("gantt_project_task_"), group_name, task_start, duration || 1, percent);

                        var group = new GanttTaskInfo(_.uniqueId("gantt_project_task_"), group_name, task_start, duration || 1, task.progress_rate);
                        _.each(task_infos, function (el) {
                            group.addChildTask(el.task_info);
                        });
                        return {task_info: group, task_start: task_start, task_stop: task_stop};
                    }
                } else {
                    var task_name = task.__name;
                    var duration_in_business_hours = false;
                    var task_start = instance.web.auto_str_to_date(task[self.fields_view.arch.attrs.date_start]);
                    if (!task_start)
                        return;
                    var task_stop;
                    if (self.fields_view.arch.attrs.date_stop) {
                        task_stop = instance.web.auto_str_to_date(task[self.fields_view.arch.attrs.date_stop]);
                        if (!task_stop)
                            task_stop = task_start;
                    } else { // we assume date_duration is defined
                        var tmp = instance.web.format_value(task[self.fields_view.arch.attrs.date_delay],
                            self.fields[self.fields_view.arch.attrs.date_delay]);
                        if (!tmp)
                            return;
                        task_stop = task_start.clone().addMilliseconds(instance.web.parse_value(tmp, {type: "float"}) * 60 * 60 * 1000);
                        duration_in_business_hours = true;
                    }
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var id = _.uniqueId("gantt_task_");
                    if (!duration_in_business_hours) {
                        duration = (duration / 24) * 8;
                    }
                    var _comment = self.fields_to_string(task, instance);
                    var task_info = new GanttTaskInfo(id, task_name, task_start, (duration) || 1, percent, undefined, _comment, null);
                    task_info.internal_task = task;
                    task_ids[id] = task_info;
                    return {task_info: task_info, task_start: task_start, task_stop: task_stop};
                }
            };
            var gantt = new GanttChart();
            _.each(_.compact(_.map(groups, function (e) {
                return generate_task_info(e, 0);
            })), function (project) {
                gantt.addProject(project);
            });
            gantt.setEditable(true);
            gantt.setImagePath("/web_gantt/static/lib/dhtmlxGantt/codebase/imgs/");
            gantt.attachEvent("onTaskEndDrag", function (task) {
                self.on_task_changed(task);
            });
            gantt.attachEvent("onTaskEndResize", function (task) {
                self.on_task_changed(task);
            });
            gantt.create(this.chart_id);

            // bind event to display task when we click the item in the tree
            $(".taskNameItem", self.$el).click(function (event) {
                var task_info = task_ids[event.target.id];
                if (task_info) {
                    self.on_task_display(task_info.internal_task);
                }
            });
            if (this.is_action_enabled('create')) {
                // insertion of create button
                var td = $($("table td", self.$el)[0]);
                var rendered = QWeb.render("GanttView-create-button");
                $(rendered).prependTo(td);
                $(".oe_gantt_button_create", this.$el).click(this.on_task_create);
            }
            // Fix for IE to display the content of gantt view.
            this.$el.find(".oe_gantt td:first > div, .oe_gantt td:eq(1) > div > div").css("overflow", "");
        },

        on_task_changed: function (task_obj) {
            var self = this;
            var itask = task_obj.TaskInfo.internal_task;
            if (!itask) {
                return;
            }
            var start = task_obj.getEST();
            var duration = task_obj.getDuration();
            var duration_in_business_hours = !!self.fields_view.arch.attrs.date_delay;
            if (!duration_in_business_hours) {
                duration = (duration / 8 ) * 24;
            }
            var end = start.clone().addMilliseconds(duration * 60 * 60 * 1000);
            var data = {};
            data[self.fields_view.arch.attrs.date_start] =
                instance.web.auto_date_to_str(start, self.fields[self.fields_view.arch.attrs.date_start].type);
            if (self.fields_view.arch.attrs.date_stop) {
                data[self.fields_view.arch.attrs.date_stop] =
                    instance.web.auto_date_to_str(end, self.fields[self.fields_view.arch.attrs.date_stop].type);
            } else { // we assume date_duration is defined
                data[self.fields_view.arch.attrs.date_delay] = duration;
            }
            this.dataset.write(itask.id, data);
        }
    });
};
