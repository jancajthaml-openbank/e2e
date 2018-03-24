require_relative 'rest_service'

class LakeAPI
  include RESTServiceHelper

  attr_reader :base_url

  def initialize()
    @base_url = "http://lake:8080" # fixme discover
  end

  def health_check()
    get("#{base_url}/health")
  end

end
