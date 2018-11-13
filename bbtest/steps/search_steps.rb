require 'json'
require_relative '../shims/deep_diff'

step "I request search" do |body|
  query = "{\"query\":\"{" + body.inspect[1..-2] + "}\",\"variables\":null,\"operationName\":null}"

  cmd = ["curl --insecure"]
  cmd << ["-X POST"]
  cmd << ["-H \"Content-Type: application/json\""]
  cmd << ["http://127.0.0.1/graphql -sw \"%{http_code}\""]
  cmd << ["-d \'#{query}\'"]

  @search_req = cmd.join(" ")
end

step "search responds with :http_status" do |http_status, body = nil|
  raise if @search_req.nil?

  @resp = Hash.new
  resp = %x(#{@search_req})

  @resp[:code] = resp[resp.length-3...resp.length].to_i
  @resp[:body] = resp[0...resp.length-3] unless resp.nil?

  expect(@resp[:code]).to eq(http_status)

  return if body.nil?

  expected_body = JSON.parse(body)

  begin
    resp_body = JSON.parse(@resp[:body])
    resp_body.deep_diff(expected_body).each do |key, array|
      (have, want) = array
      raise "unexpected attribute \"#{key}\" in response \"#{@resp[:body]}\" expected \"#{expected_body.to_json}\"" if want.nil?
      raise "\"#{key}\" expected \"#{want}\" but got \"#{have}\" instead"
    end
  rescue JSON::ParserError
    raise "invalid response got \"#{@resp[:body].strip}\", expected \"#{expected_body.to_json}\""
  end

end
