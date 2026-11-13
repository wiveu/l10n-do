import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const assetPath = process.argv[2];
assert.ok(assetPath, 'Pass the current POS JavaScript asset path');
const asset = readFileSync(assetPath, 'utf8');
const source = readFileSync(new URL('../static/src/js/models.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '');

function harness() {
    const classes = { PosOrder: class {}, PosOrderline: class {}, PosStore: class {} };
    const native = { productName: 'Synthetic item', price: '118.00', qty: '1',
        unitPrice: '100.00' };
    classes.PosOrderline.prototype.getDisplayData = () => ({ ...native });
    const context = vm.createContext({
        ...classes, Object, Array, Number, String, Boolean, Component: class {},
        _t: (value) => value, toRaw: (value) => value, OwlError: class OwlError extends Error {},
        patch(target, extension) {
            Object.setPrototypeOf(extension, { ...target });
            Object.assign(target, extension);
        },
    });
    const start = asset.indexOf('const isUnionType=');
    const end = asset.indexOf('const ObjectCreate=', start);
    assert.ok(start >= 0 && end > start);
    vm.runInContext(asset.slice(start, end), context);
    const validate = asset.indexOf('function validateProps(name,props,comp)');
    const validateEnd = asset.indexOf('function makeRefWrapper(', validate);
    assert.ok(validate >= 0 && validateEnd > validate);
    vm.runInContext(asset.slice(validate, validateEnd), context);
    const coreStart = asset.indexOf("odoo.define('@point_of_sale/app/generic_components/orderline/orderline',");
    const coreEnd = asset.indexOf('\n/* ', coreStart);
    assert.ok(coreStart >= 0 && coreEnd > coreStart);
    context.odoo = { define(_name, _dependencies, factory) {
        context.Orderline = factory(() => ({ Component: context.Component })).Orderline;
    } };
    vm.runInContext(asset.slice(coreStart, coreEnd), context);
    vm.runInContext(source, context);
    const line = new classes.PosOrderline();
    line.models = { 'account.tax': [{ id: 1, tax_group_id: [1, 'ITBIS'] },
        { id: 2, tax_group_id: [2, 'Other'] }] };
    line.order_id = { config: { l10n_do_fiscal_journal: true } };
    const validateLine = (data) => context.validateProps(context.Orderline, { line: data },
        { __owl__: { app: {} } });
    return { line, validateLine };
}

test('fiscal display data passes the actual OWL Orderline consumer', () => {
    for (const amount of [0, 18, -18, 1.8]) {
        const { line, validateLine } = harness();
        line.get_tax_details = () => ({ 1: { amount }, 2: { amount: 99 } });
        const data = line.getDisplayData();
        assert.equal(data.l10n_do_itbis, amount);
        assert.doesNotThrow(() => validateLine(data));
    }
});

test('non-fiscal display data remains valid without ITBIS', () => {
    const { line, validateLine } = harness();
    line.order_id.config.l10n_do_fiscal_journal = false;
    const data = line.getDisplayData();
    assert.equal('l10n_do_itbis' in data, false);
    assert.doesNotThrow(() => validateLine(data));
});

test('the consumer still rejects wrong tax types and unknown fields', () => {
    const { line, validateLine } = harness();
    line.get_tax_details = () => ({ 1: { amount: 18 } });
    const data = line.getDisplayData();
    assert.throws(() => validateLine({ ...data, l10n_do_itbis: '18' }), /not a number/);
    assert.throws(() => validateLine({ ...data, unexpected: true }), /unknown key 'unexpected'/);
});
