module.exports = {
  plugins: [
    require('postcss-nested'),
    require('postcss-nested-ancestors')(),
    require('autoprefixer')()
  ]
}
