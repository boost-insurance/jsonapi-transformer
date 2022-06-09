from transformers.transformers import JSONAPITransformer


class QuoteTransformer(JSONAPITransformer):
    type_name = "quote"


class CustomerTransformer(JSONAPITransformer):
    type_name = "customer"


class ProductTransformer(JSONAPITransformer):
    type_name = "product"


class AgentTransformer(JSONAPITransformer):
    type_name = "agent"


class AgencyTransformer(JSONAPITransformer):
    type_name = "agency"


class DocumentTransformer(JSONAPITransformer):
    type_name = "document"


class TermTransformer(JSONAPITransformer):
    type_name = "term"


class ProductCoverageTransformer(JSONAPITransformer):
    type_name = "product_coverage"


class ProductDeductibleTransformer(JSONAPITransformer):
    type_name = "product_deductible"


class CompanyTransformer(JSONAPITransformer):
    type_name = "company"


class ProductTypeTransformer(JSONAPITransformer):
    type_name = "product_type"


class InstallmentPlanTransformer(JSONAPITransformer):
    type_name = "installment_plan"


class DeductibleTransformer(JSONAPITransformer):
    type_name = "deductible"


class LimitTransformer(JSONAPITransformer):
    type_name = "limit"


class PolicyTransformer(JSONAPITransformer):
    type_name = "policy"


class InsuredRiskTransformer(JSONAPITransformer):
    type_name = "insured_risk"


class AgentLicenseTransformer(JSONAPITransformer):
    type_name = "agent_license"


class AgentAppointmentTransformer(JSONAPITransformer):
    type_name = "agent_appointment"


class BlacklistedEntityTransformer(JSONAPITransformer):
    type_name = "blacklisted_entity"


class AlternateIdentityTransformer(JSONAPITransformer):
    type_name = "alternate_identity"


class AddressTransformer(JSONAPITransformer):
    type_name = "address"
