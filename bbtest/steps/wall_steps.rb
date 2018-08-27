require 'json'
require_relative '../shims/deep_diff'

step "I request wall :http_method :url" do |http_method, url, body=nil|
  cmd = ["curl --insecure"]
  cmd << ["-X #{http_method.upcase}"] unless http_method.upcase == "GET"
  cmd << ["https://127.0.0.1#{url} -sw \"%{http_code}\""]
  cmd << ["-d \'#{JSON.parse(body).to_json}\'"] unless body.nil?

  @wall_req = cmd.join(" ")
end

step "wall responds with :http_status" do |http_status, body = nil|
  raise if @wall_req.nil?

  @resp = Hash.new
  resp = %x(#{@wall_req})

  @resp[:code] = resp[resp.length-3...resp.length].to_i
  @resp[:body] = resp[0...resp.length-3] unless resp.nil?

  expect(@resp[:code]).to eq(http_status)

  return if body.nil?

  expected_body = JSON.parse(body)

  begin
    resp_body = JSON.parse(@resp[:body])
    resp_body.deep_diff(expected_body).each do |key, array|
      (have, want) = array
      raise "unexpected attribute \"#{key}\" in response \"#{@resp.body}\" expected \"#{expected_body.to_json}\"" if want.nil?
      raise "\"#{key}\" expected \"#{want}\" but got \"#{have}\" instead"
    end
  rescue JSON::ParserError
    raise "invalid response got \"#{@resp.body.strip}\", expected \"#{expected_body.to_json}\""
  end

end
