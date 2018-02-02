require 'thread'

class Hash

  def deep_diff(b)
    a = self
    (a.keys | b.keys).each_with_object({}) do |k, diff|
      if a[k] != b[k]
        if a[k].respond_to?(:deep_diff) && b[k].respond_to?(:deep_diff)
          diff[k] = a[k].deep_diff(b[k])
        else
          diff[k] = [a[k], b[k]]
        end
      end
    end
  end

end

module Enumerable

  def par
    parallelism = (Integer(%x(getconf _NPROCESSORS_ONLN)) rescue 1) << 3

    work = Queue.new
    each { |x| work << [x] }
    parallelism.times { work << nil }

    (1..parallelism).map {
      Thread.new{
        while x = work.deq ; yield(x[0])
        end
      }
    }.each(&:join)
  end

end
