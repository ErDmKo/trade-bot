const helpers = require('./helpers');
const webpack = require('webpack');

const AssetsPlugin = require('assets-webpack-plugin');
const ContextReplacementPlugin = require('webpack/lib/ContextReplacementPlugin');
const CommonsChunkPlugin = require('webpack/lib/optimize/CommonsChunkPlugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const ForkCheckerPlugin = require('awesome-typescript-loader').ForkCheckerPlugin;

const HMR = helpers.hasProcessFlag('hot');
const METADATA = {
  title: 'Trade bot monitor',
  baseUrl: '/',
  isDevServer: helpers.isWebpackDevServer()
};

module.exports = function (options) {
    const isProd = options.env === 'production';
    return {
        entry: {
            'polyfills': './front/polyfills.browser.ts',
            'vendor': './front/vendor.browser.ts',
            'main': './front/main.browser.ts'
        },
        resolve: {
            extensions: ['.ts', '.js', '.json'],
            modules: [helpers.root('front'), 'node_modules'],
        },
        module: {
            rules: [{
                test: /\.html$/,
                use: 'raw-loader',
                exclude: [helpers.root('front/index.html')]
            }, {
                test: /\.ts$/,
                loaders: [
                    '@angularclass/hmr-loader?pretty=' + !isProd + '&prod=' + isProd,
                    'awesome-typescript-loader',
                    'angular2-template-loader'
                ],
                exclude: [/\.(spec|e2e)\.ts$/]
            }, {
                test: /\.css$/,
                loaders: ['to-string-loader', 'css-loader', 'postcss-loader']
            }, {
                test: /\.(jpg|png|gif)$/,
                loader: 'file'
            }]
        }, plugins: [new AssetsPlugin({
            path: helpers.root('server/static'),
            filename: 'webpack-assets.json',
            prettyPrint: true
        }), new ForkCheckerPlugin(), new CommonsChunkPlugin({
            name: ['vendor', 'polyfills']
        }), new ContextReplacementPlugin(
            /angular(\\|\/)core(\\|\/)(esm(\\|\/)front|front)(\\|\/)linker/,
            helpers.root('front') // location of your src
        ), new CopyWebpackPlugin([{
               from: 'front/assets',
               to: 'server/static',
            }, {
               from: 'front/meta',
               to: 'server/meta',
            },
        ])], node: {
            global: true,
            crypto: 'empty',
            process: true,
            module: false,
            clearImmediate: false,
            setImmediate: false
        }
    }
}
