module CustomFilters
    def starts_with(input, prefix)
      input.start_with?(prefix)
    end
  end
  
  Liquid::Template.register_filter(CustomFilters)

  