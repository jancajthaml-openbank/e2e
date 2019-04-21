require 'json'
require 'json-diff'
require 'deepsort'

step "I request curl :http_method :url" do |http_method, url, body=nil|
  cmd = ["curl --insecure"]
  cmd << ["-X #{http_method.upcase}"] unless http_method.upcase == "GET"
  cmd << ["-H \"Content-Type: application/json\""]
  cmd << ["#{url} -sw \"%{http_code}\""]
  cmd << ["-d \'#{JSON.parse(body).to_json}\'"] unless body.nil?

  @http_req = cmd.join(" ")
end

step "curl responds with :http_status" do |http_status, body = nil|
  raise if @http_req.nil?

  @resp = { :code => 0 }

  eventually(timeout: 10, backoff: 1) {
    resp = %x(#{@http_req})
    @resp[:code] = resp[resp.length-3...resp.length].to_i
    raise "endpoint unreachable" if @resp[:code] === 0
    @resp[:body] = resp[0...resp.length-3] unless resp.nil?
  }

  expect(@resp[:code]).to eq(http_status)

  return if body.nil?

  expectation = JSON.parse(body)
  expectation.deep_sort!

  begin
    resp_body = JSON.parse(@resp[:body])
    resp_body.deep_sort!

    diff = JsonDiff.diff(resp_body, expectation).select { |item| item["op"] == "add" }.map { |item| item["value"] or item }
    return if diff == []

    raise "expectation failure:\ngot:\n#{JSON.pretty_generate(resp_body)}\nexpected:\n#{JSON.pretty_generate(expectation)}"

  rescue JSON::ParserError
    raise "invalid response got \"#{@resp[:body].strip}\", expected \"#{expectation.to_json}\""
  end

end
