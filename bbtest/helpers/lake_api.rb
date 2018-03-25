require_relative 'rest_service'

class LakeAPI
  include RESTServiceHelper

  def health_check()
    get("http://lake:8080/health")
  end

end
