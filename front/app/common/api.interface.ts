export interface IBaseBalance {
    rights?: {
        info: string,
        trade: string
        withdraw: string
    },
    transaction_count?: string,
    open_orders?: string
    server_time?: string
}
export interface IBalance extends IBaseBalance {
    funds?: {
        [currency: string]: string
    }
}
