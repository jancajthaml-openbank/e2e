require_relative 'placeholders'

step "file :directory should exist" do |path|
  unless File.file?(path)
    raise "file:  #{path} is a directory" if File.directory?(path)
    raise "file:  #{path} was not found\nfiles: #{Dir[File.dirname(path)+"/*"]}"
  end
end

step "directory :directory should contain :count files" do |path, count|
  files = Dir["#{path}/*"].reject { |f| File.directory?(f) }
  raise "expected  #{count} files, actual is #{files.length}\nfiles:    #{files}" unless files.length == count
end
