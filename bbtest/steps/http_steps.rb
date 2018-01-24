require 'json'
require 'excon'

# fixme add with timeout as a parameter
step "I call :http_method :url" do |http_method, url, body = nil|
  case http_method
  when "get"
    @resp = Excon.get(url, :read_timeout => 5, :write_timeout => 5)
  when "post"
    @resp = Excon.post(url, :headers => {
      'Content-Type' => 'application/json;charset=utf8'
    }, :body => body, :read_timeout => 5, :write_timeout => 5)
  else
    raise "undefined method #{http_method.upcase}"
  end

end

step "response status should be :http_status" do |http_status|
  expect(@resp.status).to be http_status
end

step "response content should be:" do |content|
  expected_body = JSON.parse(content)

  begin
    resp_body = JSON.parse(@resp.body)
    resp_body.deep_diff(expected_body).each do |key, array|
      (have, want) = array
      if want.nil?
        raise "unexpected attribute \"#{key}\" in response \"#{@resp.body}\" expected \"#{expected_body.to_json}\""
      else
        raise "\"#{key}\" expected \"#{want}\" but got \"#{have}\" instead"
      end
    end
  rescue JSON::ParserError
    raise "invalid response got \"#{@resp.body.strip}\", expected \"#{expected_body.to_json}\""
  end
end

# input matching

# fixme add timeout input matching
placeholder :http_method do
  match(/(GET|get|POST|post|PATCH|patch)/) do |http_method|
    http_method.downcase
  end
end

placeholder :http_status do
  match(/\d{3}/) do |http_status|
    http_status.to_i
  end
end

placeholder :url do
  match(/https?:\/\/[\S]+/) do |url|
    url
  end
end


