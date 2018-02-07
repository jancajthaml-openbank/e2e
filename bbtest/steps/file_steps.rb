require_relative 'placeholders'

step "file :path should exist" do |path|
  abspath = "/data/#{@tenant_id}#{path}"
  unless File.file?(abspath)
    raise "file:  #{abspath} is a directory" if File.directory?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end
end

step "directory :path should contain :count files" do |path, count|
  abspath = "/data/#{@tenant_id}#{path}"
  files = Dir["#{abspath}/*"].reject { |f| File.directory?(f) }
  raise "expected  #{count} files, actual is #{files.length}\nfiles:    #{files}" unless files.length == count
end
