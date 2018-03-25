require_relative 'rest_service'

class ReportingAPI
  include RESTServiceHelper

  def graphql(req)
    post("http://reporting_#{$tenant_id}:8080/graphql", req)
  end

  def health_check()
    %x(nc -z reporting_#{$tenant_id} 8080 2> /dev/null)
  end

end
