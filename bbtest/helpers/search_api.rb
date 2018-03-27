require_relative 'rest_service'

class SearchAPI
  include RESTServiceHelper

  def graphql(req)
    post("http://search_#{$tenant_id}:8080/graphql", req)
  end

  def health_check()
    get("http://search_#{$tenant_id}:8080/health")
  end

end
