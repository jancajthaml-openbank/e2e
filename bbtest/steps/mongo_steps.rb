require 'json'
require 'mongo'

step "mongo collection :coll should contain" do |coll, data|
  raw = JSON.parse(data.gsub(/\{\s+\"\$numberDecimal\": \"(.+)\"\s+\}/, '\1'))
  matches = data.match(/\"(.+)\"\:\s\{\s+\"\$numberDecimal\": \"(.+)\"\s+\},/)
  key, val = matches.captures unless matches.nil?

  raw[key] = BSON::Decimal128.from_string(val) if (key and val)

  if raw.kind_of?(Array)
    raw.each { |pivot|
      begin
        eventually(timeout: 6) {
          result = []
          MongoHelper.mongo_find(coll, pivot).each { |item| result << item }
          raise "no data found" if result.empty?
        }
      rescue => _
        actual = []
        MongoHelper.mongo_find(coll).each { |item| actual << item }
        raise "search query: #{pivot}, coll: \"#{coll}\", actual contents: #{actual}"
      end
    }
  else
    begin
      eventually(timeout: 6) {
        result = []
        MongoHelper.mongo_find(coll, raw).each { |item| result << item }
        raise "no data found" if result.empty?
      }
    rescue => _
      actual = []
      MongoHelper.mongo_find(coll).each { |item| actual << item }
      raise "search query: #{raw}, coll: \"#{coll}\", actual contents: #{actual}"
    end
  end
end

