from knack.help_files import _load_help_file
from collections import OrderedDict
from .utilities import AZDevTransDeprecateInfo, AZDevTransValidator, AZDevTransNode


class AZDevTransCommandHelp(AZDevTransNode):

    def __init__(self, description, help_data):
        try:
            self.short_summary = description[:description.index('.')]
            long_summary = description[description.index('.') + 1:].lstrip()
            self.long_summary = ' '.join(long_summary.splitlines())
        except (ValueError, AttributeError):
            self.short_summary = description

        if help_data:
            assert help_data['type'].lower() == 'command'
            short_summary = help_data.get('short-summary', None)
            long_summary = help_data.get('long-summary', None)
            if short_summary:
                self.short_summary = short_summary
            if long_summary:
                self.long_summary = long_summary
            assert self.short_summary

    def to_config(self, ctx):
        key = 'help'
        value = OrderedDict()
        if self.short_summary:
            value['short-summary'] = self.short_summary
        if self.long_summary:
            value['long-summary'] = self.long_summary

        if set(value.keys()) == {"short-summary"}:
            value = value['short-summary']
        return key, value


class AZDevTransCommandExamples(AZDevTransNode):

    def __init__(self, examples):

        self.examples = {}
        for example in examples:
            raw_name = example['name']
            text = example['text']
            autogenerated = "(autogenerated)" in raw_name
            name = raw_name.replace("(autogenerated)", "").strip()
            if name in self.examples:
                raise TypeError('Duplicated example name: "{}"'.format(raw_name))
            self.examples[name] = {
                'name': name,
                'text': text,
                'autogenerated': autogenerated
            }

    def to_config(self, ctx):
        key = 'examples'
        values = []
        example_keys = []
        autogenerated_example_keys = []
        for k, v in self.examples.keys():
            if not v['autogenerated']:
                example_keys.append(k)
            else:
                autogenerated_example_keys.append(k)
        for k in sorted(example_keys):
            v = self.examples[k]
            value = OrderedDict()
            value['name'] = v['name']
            value['text'] = v['text']
            values.append(value)
        for k in sorted(autogenerated_example_keys):
            v = self.examples[k]
            value = OrderedDict()
            value['autogenerated'] = True
            value['name'] = v['name']
            value['text'] = v['text']
            values.append(value)
        return key, values


class AZDevTransClientFactory(AZDevTransNode):

    def __init__(self, client_factory):
        from azure.cli.core.translator.client_factory import AzClientFactory
        if not isinstance(client_factory, AzClientFactory):
            raise TypeError('Client factory is not an instance of "AzClientFactory", get "{}"'.format(
                type(client_factory)))
        self.client_factory = client_factory

    def to_config(self, ctx):
        from azure.cli.core.translator.client_factory import AzClientFactory
        key = "client-factory"
        if isinstance(self.client_factory, AzClientFactory):
            value = ctx.get_import_path(self.client_factory.module_name, self.client_factory.name)
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransNoWait(AZDevTransNode):
    DEFAULT_NO_WAIT_PARAM_DEST = 'no_wait'

    def __init__(self, param):
        self.no_wait_param = param

    def to_config(self, ctx):
        if self.no_wait_param == self.DEFAULT_NO_WAIT_PARAM_DEST:
            return 'support-no-wait', True
        else:
            return 'no-wait-param', self.no_wait_param


class AZDevTransCommandOperation(AZDevTransNode):

    def __init__(self, command_operation):
        from azure.cli.core.commands.command_operation import BaseCommandOperation
        if not isinstance(command_operation, BaseCommandOperation):
            raise TypeError('Command operation is not an instant of "BaseCommandOperation", get "{}"'.format(
                type(command_operation)))
        self.command_operation = command_operation

    def to_config(self, ctx):
        from azure.cli.core.commands.command_operation import CommandOperation, WaitCommandOperation,\
            ShowCommandOperation, GenericUpdateCommandOperation
        if isinstance(self.command_operation, CommandOperation):
            key = "operation"
            value = ctx.simplify_import_path(self.command_operation.operation)
        elif isinstance(self.command_operation, WaitCommandOperation):
            key = "wait-operation"
            value = ctx.simplify_import_path(self.command_operation.operation)
        elif isinstance(self.command_operation, ShowCommandOperation):
            key = "show-operation"
            value = ctx.simplify_import_path(self.command_operation.operation)
        elif isinstance(self.command_operation, GenericUpdateCommandOperation):
            key = "generic-update"
            value = OrderedDict()
            value['getter-operation'] = ctx.simplify_import_path(self.command_operation.getter_operation)
            value['setter-operation'] = ctx.simplify_import_path(self.command_operation.setter_operation)
            value['setter-arg-name'] = self.command_operation.setter_arg_name
            if self.command_operation.custom_function_op:
                value['custom-function-operation'] = ctx.simplify_import_path(self.command_operation.custom_function_op)
            if self.command_operation.child_collection_prop_name:
                child_value = OrderedDict()
                child_value['collection-prop-name'] = self.command_operation.child_collection_prop_name
                child_value['collection-key'] = self.command_operation.child_collection_key
                child_value['arg-name'] = self.command_operation.child_arg_name
                value['child'] = child_value
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransTransform(AZDevTransNode):

    def __init__(self, transform):
        from azure.cli.core.translator.transformer import AzTransformer
        if not isinstance(transform, AzTransformer):
            raise TypeError('Transform is not an instance of "AzTransformer", get "{}"'.format(
                type(transform)))
        self.transform = transform

    def to_config(self, ctx):
        from azure.cli.core.translator.transformer import AzFuncTransformer
        key = 'transform'
        if isinstance(transform, AzFuncTransformer):
            value = ctx.get_import_path(self.transform.module_name, self.transform.name)
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransTableTransformer(AZDevTransNode):

    def __init__(self, table_transformer):
        from azure.cli.core.translator.transformer import AzTransformer
        if not isinstance(table_transformer, str) and not isinstance(table_transformer, AzTransformer):
            raise TypeError('Table transform is not a string or an instance of "AzTransformer", get "{}"'.format(
                type(table_transformer)))
        self.table_transformer = table_transformer

    def to_config(self, ctx):
        from azure.cli.core.translator.transformer import AzFuncTransformer
        key = 'table-transformer'
        if isinstance(ctx, AzFuncTransformer):
            value = ctx.get_import_path(self.table_transformer.module_name, self.table_transformer.name)
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransExceptionHandler(AZDevTransNode):

    def __init__(self, exception_handler):
        from azure.cli.core.translator.exception_handler import AzExceptionHandler
        if not isinstance(exception_handler, AzExceptionHandler):
            raise TypeError('Exception handler is not an instance of "AzExceptionHandler", get "{}"'.format(
                type(exception_handler)))
        self.exception_handler = exception_handler

    def to_config(self, ctx):
        from azure.cli.core.translator.exception_handler import AzFuncExceptionHandler
        key = 'exception-handler'
        if isinstance(exception_handler, AzFuncExceptionHandler):
            value = ctx.get_import_path(self.exception_handler.module_name, self.exception_handler.name)
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransResourceType(AZDevTransNode):

    def __init__(self, resource_type):
        from azure.cli.core.profiles import ResourceType, CustomResourceType, PROFILE_TYPE
        if isinstance(resource_type, ResourceType):
            pass
        elif isinstance(resource_type, CustomResourceType):
            # used for extensions. it will call register_resource_type.
            pass
        elif resource_type == PROFILE_TYPE:
            # used only in commands: ad sp | ad app | feature
            # TODO: Deprecate this value. Don't need this for profile specific configuration
            raise NotImplementedError()
        else:
            raise TypeError("Not supported resource_type type {}".format(type(resource_type)))
        self.resource_type = resource_type

    def to_config(self, ctx):
        from azure.cli.core.profiles import ResourceType
        key = 'resource-type'
        if isinstance(self.resource_type, ResourceType):
            value = self.resource_type.name
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransCommand(AZDevTransNode):
    # supported: 'confirmation', 'no_wait_param', 'supports_no_wait', 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'deprecate_info',
    # 'table_transformer', 'exception_handler', 'client_factory', 'transform', 'validator', 'supports_local_cache', 'min_api', 'max_api',

    # PendingForDeprecation: 'client_arg_name', 'model_path', 'resource_type', 'operation_group',
    # TODO: parse operation combine operation template and function name

    # ignored: 'doc_string_source', 'local_context_attribute', 'custom_command_type', 'command_type',

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name

        self.sub_arguments = {}

        self._parse_deprecate_info(table_instance)
        self._parse_is_preview(table_instance)
        self._parse_is_experimental(table_instance)
        assert not (self.is_preview and self.is_experimental)

        self._parse_confirmation(table_instance)
        self._parse_no_wait(table_instance)

        self._parse_min_api(table_instance)
        self._parse_max_api(table_instance)
        self._parse_resource_type(table_instance)
        self._parse_operation_group(table_instance)

        self._parse_client_arg_name(table_instance)

        self._parse_supports_local_cache(table_instance)
        self._parse_model_path(table_instance)

        self._parse_operation(table_instance)
        self._parse_client_factory(table_instance)

        self._parse_validator(table_instance)
        self._parse_transform(table_instance)
        self._parse_table_transformer(table_instance)
        self._parse_exception_handler(table_instance)

        self._parse_help_and_examples(table_instance)

    def _parse_deprecate_info(self, table_instance):
        deprecate_info = table_instance.deprecate_info
        if deprecate_info is not None:
            deprecate_info = AZDevTransDeprecateInfo(deprecate_info)
        self.deprecate_info = deprecate_info

    def _parse_is_preview(self, table_instance):
        if table_instance.preview_info:
            self.is_preview = True
        else:
            self.is_preview = False

    def _parse_is_experimental(self, table_instance):
        if table_instance.experimental_info:
            self.is_experimental = True
        else:
            self.is_experimental = False

    def _parse_confirmation(self, table_instance):
        if table_instance.confirmation:
            self.confirmation = True
        else:
            self.confirmation = False

    def _parse_no_wait(self, table_instance):
        no_wait_param = None
        if table_instance.supports_no_wait:
            no_wait_param = AZDevTransNoWait.DEFAULT_NO_WAIT_PARAM_DEST
        if table_instance.no_wait_param:
            no_wait_param = table_instance.no_wait_param
        self.no_wait = AZDevTransNoWait(no_wait_param) if no_wait_param else None

    def _parse_operation(self, table_instance):
        command_operation = table_instance.command_kwargs.get('command_operation', None)
        if command_operation is not None:
            command_operation = AZDevTransCommandOperation(command_operation)
        self.operation = command_operation

    def _parse_client_factory(self, table_instance):
        client_factory = table_instance.command_kwargs.get('client_factory', None)
        if client_factory is not None:
            client_factory = AZDevTransClientFactory(client_factory)
        self.client_factory = client_factory

    def _parse_validator(self, table_instance):
        validator = table_instance.validator
        if validator is not None:
            validator = AZDevTransValidator(validator)
        self.validator = validator

    def _parse_transform(self, table_instance):
        transform = table_instance.command_kwargs.get('transform', None)
        if transform is not None:
            transform = AZDevTransTransform(transform)
        self.transform = transform

    def _parse_table_transformer(self, table_instance):
        table_transformer = table_instance.table_transformer
        if isinstance(table_transformer, str):
            table_transformer = table_transformer.strip()
            if not table_transformer:
                table_transformer = None
        if table_transformer is not None:
            table_transformer = AZDevTransTableTransformer(table_transformer)
        self.table_transformer = table_transformer

    def _parse_exception_handler(self, table_instance):
        exception_handler = table_instance.exception_handler
        if exception_handler is not None:
            exception_handler = AZDevTransExceptionHandler(exception_handler)
        self.exception_handler = exception_handler

    def _parse_supports_local_cache(self, table_instance):
        supports_local_cache = table_instance.command_kwargs.get('supports_local_cache', False)
        assert isinstance(supports_local_cache, bool)
        self.supports_local_cache = supports_local_cache

    def _parse_min_api(self, table_instance):
        min_api = table_instance.command_kwargs.get('min_api', None)
        assert min_api is None or isinstance(min_api, str)
        self.min_api = min_api

    def _parse_max_api(self, table_instance):
        max_api = table_instance.command_kwargs.get('max_api', None)
        assert max_api is None or isinstance(max_api, str)
        self.max_api = max_api

    def _parse_resource_type(self, table_instance):
        resource_type = table_instance.command_kwargs.get('resource_type', None)
        if resource_type is not None:
            resource_type = AZDevTransResourceType(resource_type)
        self.resource_type = resource_type

    def _parse_operation_group(self, table_instance):
        operation_group = table_instance.command_kwargs.get('operation_group', None)
        assert operation_group is None or isinstance(operation_group, str)
        self.operation_group = operation_group

    def _parse_help_and_examples(self, table_instance):
        description = table_instance.description
        if callable(description):
            description = description()
        assert isinstance(description, str)
        help_data = _load_help_file(self.full_name)
        self.help = AZDevTransCommandHelp(description, help_data)

        examples = None
        if help_data:
            if 'examples' in help_data:
                examples = help_data['examples']
            elif 'example' in help_data:
                examples = help_data['example']

        if examples is not None:
            examples = AZDevTransCommandExamples(examples)
        self.examples = examples

        parameters_help_data = {}
        if help_data:
            if 'parameters' in help_data:
                for parameter in help_data['parameters']:
                    parameters_help_data[parameter['name']] = parameter
        self.parameters_help_data = parameters_help_data

    def _parse_model_path(self, table_instance):
        # TODO: Deprecate this parameter, Only `network front-door waf-policy` command group used.
        model_path = table_instance.command_kwargs.get('model_path', None)
        assert model_path is None or isinstance(model_path, str)
        self.model_path = model_path

    def _parse_client_arg_name(self, table_instance):
        # TODO: Deprecate this parameter, because it's only for eventgrid track1 SDK usage
        client_arg_name = table_instance.command_kwargs.get('client_arg_name', None)
        assert client_arg_name is None or isinstance(client_arg_name, str)
        if client_arg_name is not None:
            if client_arg_name == 'client':
                client_arg_name = None
        self.client_arg_name = client_arg_name

    def to_config(self, ctx):
        pass
